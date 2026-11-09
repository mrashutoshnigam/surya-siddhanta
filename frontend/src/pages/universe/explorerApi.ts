import type { Catalog, MarsLesson, Model, Snapshot, Trajectory } from "./types";
import { iso } from "./math";

async function request<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api/explorer/${path}`, {
    method: body ? "POST" : "GET", signal,
    headers: body ? {"Content-Type":"application/json"} : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : `Could not load this part of the universe (${response.status}).`);
  }
  return response.json();
}

export const explorerApi = {
  marsLesson:(signal?:AbortSignal)=>request<MarsLesson>('lessons/mars-retrograde',undefined,signal),
  catalog: (signal?: AbortSignal) => request<Catalog>("catalog", undefined, signal),
  snapshot: (model: Model, time: number, signal?: AbortSignal) => request<Snapshot>("snapshot", {model, instant:iso(time)}, signal),
  trajectory: (model: Model, start: number, days: number, signal?: AbortSignal) => request<Trajectory>("trajectory", {model,start:iso(start),days}, signal),
};
