import { useEffect, useState } from "react";

/**
 * Build the pair of probe hooks for one chapter's probe route.
 *
 * `send` posts one slider request and resolves to the JSON answer. The hooks
 * are debounced by 120 ms so dragging a slider sends one request per pause.
 * An answer is stored with the request it answers and returned only while
 * that request is still current, so a card can never pair a new input with
 * an old answer.
 */
export function makeProbe(send: (body: Record<string, unknown>) => Promise<unknown>) {
  /**
   * The exact-match answer for `request`: `null` while pending, on failure,
   * and when `request` is `null` (which sends nothing).
   */
  function useProbe<T>(request: Record<string, unknown> | null): T | null {
    const [answer, setAnswer] = useState<{ key: string; value: T } | null>(null);
    const key = request === null ? null : JSON.stringify(request);

    useEffect(() => {
      if (key === null) return undefined;
      let cancelled = false;
      const timer = setTimeout(() => {
        send(JSON.parse(key))
          .then((result) => {
            if (!cancelled) setAnswer({ key, value: result as T });
          })
          .catch(() => {
            /* leave the card in its pending state */
          });
      }, 120);
      return () => {
        cancelled = true;
        clearTimeout(timer);
      };
    }, [key]);

    return answer !== null && answer.key === key ? answer.value : null;
  }

  /**
   * Like `useProbe`, but for single-source panels where a 120 ms lag is
   * harmless: the newest exact-match answer, else the previous one, else `seed`.
   */
  function useLastProbe<T>(request: Record<string, unknown>, seed: T): T {
    const fresh = useProbe<T>(request);
    const [last, setLast] = useState<T>(seed);
    useEffect(() => {
      if (fresh !== null) setLast(fresh);
    }, [fresh]);
    return fresh ?? last;
  }

  return { useProbe, useLastProbe };
}
