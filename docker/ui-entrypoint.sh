#!/bin/sh
# Entrypoint for the single-image (UI-only) Surya Siddhanta deployment.
#
# Starts two processes:
#   * uvicorn, bound to 127.0.0.1:$API_PORT  -- internal, never published
#   * nginx,   listening on $PORT (and 443 when ENABLE_TLS=1) -- the only
#              exposed surface
#
# Environment:
#   PORT         public http port (default 80). Render sets this itself
#                (10000 by default) and routes its HTTPS edge to it.
#   ENABLE_TLS   1 to also serve https on 443 with the certificate in
#                /etc/nginx/certs. Defaults to 0 on Render, which terminates
#                TLS before traffic reaches the container, and to 1 elsewhere.
#   API_PORT     loopback port for the FastAPI backend (default 8000)
#   API_WORKERS  uvicorn worker count -- keep this at 1 (the default) unless
#                the chat session store moves out of process memory:
#                api/chat.py holds one agent per browser session in a plain
#                dict, so a second worker loses half the conversations.
#   FORCE_HTTPS  1 to 301-redirect http to https (default 0), except
#                /api/health so health probes keep working. Safe behind
#                Render: the redirect keys on X-Forwarded-Proto, not on the
#                plain-http hop from Render's edge.
#   TLS_CN       common name for the generated self-signed cert (default localhost)
#   BACKEND_START_TIMEOUT
#                seconds to wait for uvicorn to listen before giving up
#                (default 180)
set -e

PORT="${PORT:-80}"
API_PORT="${API_PORT:-8000}"
API_WORKERS="${API_WORKERS:-1}"
CERT_DIR=/etc/nginx/certs

# Render sets RENDER=true in every service's environment.
if [ -z "${ENABLE_TLS:-}" ]; then
    if [ "${RENDER:-}" = "true" ]; then ENABLE_TLS=0; else ENABLE_TLS=1; fi
fi

if [ "$PORT" = "$API_PORT" ]; then
    echo "entrypoint: PORT and API_PORT are both $PORT; set API_PORT to a different port" >&2
    exit 1
fi
if [ "$ENABLE_TLS" = "1" ] && [ "$PORT" = "443" ]; then
    echo "entrypoint: PORT=443 collides with the TLS listener; set ENABLE_TLS=0 or change PORT" >&2
    exit 1
fi

# --- nginx config ---------------------------------------------------------
mkdir -p /etc/nginx/snippets
sed -e "s/__PORT__/$PORT/g" -e "s/__API_PORT__/$API_PORT/g" \
    /etc/nginx/templates/ss.conf > /etc/nginx/conf.d/default.conf

if [ "$ENABLE_TLS" = "1" ]; then
    cp /etc/nginx/templates/ss-tls.conf /etc/nginx/snippets/tls-server.conf

    # Mount a real key pair over $CERT_DIR to use it; otherwise generate a
    # self-signed pair so :443 works out of the box for local use.
    if [ ! -s "$CERT_DIR/server.crt" ] || [ ! -s "$CERT_DIR/server.key" ]; then
        echo "entrypoint: no certificate in $CERT_DIR, generating a self-signed one" >&2
        mkdir -p "$CERT_DIR"
        openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
            -keyout "$CERT_DIR/server.key" -out "$CERT_DIR/server.crt" \
            -subj "/CN=${TLS_CN:-localhost}" \
            -addext "subjectAltName=DNS:${TLS_CN:-localhost},DNS:localhost,IP:127.0.0.1" \
            >/dev/null 2>&1
        chmod 600 "$CERT_DIR/server.key"
    fi
    listening=":$PORT and :443"
else
    : > /etc/nginx/snippets/tls-server.conf
    listening=":$PORT (TLS terminated upstream)"
fi

if [ "${FORCE_HTTPS:-0}" = "1" ]; then
    echo 'if ($ss_redirect_https) { return 301 https://$host$request_uri; }' \
        > /etc/nginx/snippets/force-https.conf
else
    : > /etc/nginx/snippets/force-https.conf
fi

nginx -t -q

# --- process helpers --------------------------------------------------------
# Liveness is read from /proc rather than probed with `kill -0`. Signalling a
# process owned by another uid needs CAP_KILL, which hardened runtimes such as
# Render's drop: there `kill -0` on the ssapp-owned backend fails with EPERM,
# the old loop read that as "backend died", and the container exited before
# uvicorn had finished importing. /proc needs no privilege at all.

# True while pid $1 exists and is not a zombie.
alive() {
    [ -r "/proc/$1/stat" ] || return 1
    # Field 3 is the state; strip through ") " first since the command name in
    # field 2 may itself contain spaces.
    state=$(sed 's/^.*) //' "/proc/$1/stat" 2>/dev/null | cut -d' ' -f1)
    [ -n "$state" ] && [ "$state" != "Z" ]
}

# True once something is in LISTEN state (0A) on local port $1. Read from
# /proc/net so the wait loop costs a grep, not a python start per tick -- on a
# 0.1-CPU instance that start competes with the very import it is waiting on.
listening_on() {
    hex=$(printf '%04X' "$1")
    cat /proc/net/tcp /proc/net/tcp6 2>/dev/null \
        | awk -v p=":$hex" '$2 ~ p"$" && $4 == "0A" { found = 1 } END { exit !found }'
}

# --- backend --------------------------------------------------------------
# The backend runs as ssapp and nginx's workers as www-data; both switches need
# CAP_SETUID/CAP_SETGID. Check once, up front, so a runtime that strips them
# fails with a message naming the cause instead of nginx workers dying one by
# one behind a master process that still looks alive.
if ! setpriv --reuid=ssapp --regid=ssapp --init-groups true 2>/dev/null; then
    echo "entrypoint: cannot switch users (CAP_SETUID/CAP_SETGID unavailable); both the backend (ssapp) and nginx workers (www-data) need it" >&2
    exit 1
fi

# setpriv execs in place, so $! below is uvicorn's own pid.
setpriv --reuid=ssapp --regid=ssapp --init-groups \
    python -m uvicorn suryasiddhanta.api.main:app \
        --host 127.0.0.1 --port "$API_PORT" --workers "$API_WORKERS" &
api_pid=$!

# Best effort: without CAP_KILL the backend cannot be signalled across uids,
# but once this script (PID 1) exits the runtime tears the container down and
# the backend with it. It holds no durable state, so nothing is lost.
term() {
    kill "$api_pid" 2>/dev/null || true
    nginx -s quit 2>/dev/null || true
}
trap term TERM INT

# Fail loudly rather than serving a UI whose every call 502s. The budget is
# generous because a 0.1-CPU instance imports numpy + fastapi + anthropic
# slowly; BACKEND_START_TIMEOUT overrides it.
timeout="${BACKEND_START_TIMEOUT:-180}"
i=0
while ! listening_on "$API_PORT"; do
    if ! alive "$api_pid"; then
        rc=0
        wait "$api_pid" 2>/dev/null || rc=$?
        echo "entrypoint: backend exited with status $rc before listening on 127.0.0.1:$API_PORT" >&2
        term
        exit 1
    fi
    i=$((i + 1))
    if [ "$i" -ge "$timeout" ]; then
        echo "entrypoint: backend still not listening on 127.0.0.1:$API_PORT after ${timeout}s" >&2
        term
        exit 1
    fi
    sleep 1
done
echo "entrypoint: backend up on 127.0.0.1:$API_PORT after ~${i}s; starting nginx on $listening" >&2

nginx -g 'daemon off;' &
nginx_pid=$!

# Exit as soon as either process dies, so the container restarts as a unit
# instead of silently serving half a stack.
while alive "$api_pid" && alive "$nginx_pid"; do
    sleep 2
done

echo "entrypoint: a supervised process exited, shutting down" >&2
term
exit 1
