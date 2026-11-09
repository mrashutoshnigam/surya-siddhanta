"""Start a development service, or reuse it when it is already healthy."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("service", choices=("api", "frontend"))
    parser.add_argument("--port", type=int, help="Override the service port")
    args = parser.parse_args()
    service = args.service
    is_api = service == "api"
    port = args.port if args.port is not None else (8000 if is_api else 5173)
    url = f"http://127.0.0.1:{port}"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    try:
        with opener.open(url + ("/health" if is_api else "/"), timeout=3) as response:
            body = response.read().decode("utf-8")
        if is_api:
            payload = json.loads(body)
            healthy = isinstance(payload, dict) and payload.get("status") == "ok"
        else:
            healthy = "Surya Siddhanta Explorer" in body
        if not healthy:
            print(f"Port {port} is occupied by an unexpected service.", file=sys.stderr)
            return 1
        ready = "Application startup complete" if is_api else "VITE ready in 0 ms"
        print(f"{ready} (reusing {url})", flush=True)
        return 0
    except urllib.error.HTTPError as error:
        print(f"Service on {url} returned HTTP {error.code}.", file=sys.stderr)
        return 1
    except urllib.error.URLError as error:
        if not isinstance(error.reason, ConnectionRefusedError):
            print(f"Cannot check {url}: {error.reason}", file=sys.stderr)
            return 1
    except (ValueError, TimeoutError, OSError) as error:
        print(f"Cannot check {url}: {error}", file=sys.stderr)
        return 1

    if is_api:
        command = [sys.executable, "-m", "uvicorn", "suryasiddhanta.api.main:app",
                   "--reload", "--host", "127.0.0.1", "--port", str(port)]
        cwd = ROOT
    else:
        node = shutil.which("node")
        vite = ROOT / "frontend/node_modules/vite/bin/vite.js"
        if not node or not vite.is_file():
            print("Install Node.js and run Install Frontend Dependencies first.", file=sys.stderr)
            return 1
        command = [node, str(vite), "--host", "127.0.0.1", "--port", str(port), "--strictPort"]
        cwd = ROOT / "frontend"

    try:
        return subprocess.call(command, cwd=cwd)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
