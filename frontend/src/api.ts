import type { EjectResponse, SimulateResponse } from "./types/telemetry";

async function post<T>(path: string): Promise<T> {
  const res = await fetch(path, { method: "POST" });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* non-JSON error body: keep status text */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

export const SIM_DRIVE = "Z:\\";
export const simulate = () => post<SimulateResponse>("/api/demo/simulate");
export const eject = () => post<EjectResponse>(`/api/demo/eject?drive=${encodeURIComponent(SIM_DRIVE)}`);
