import type { FileScannedEvent } from "../types/telemetry";
import { TIER_HEX } from "../lib/tier";

const W = 640;
const H = 240;
const PAD = { l: 34, r: 10, t: 12, b: 22 };
const THRESHOLD = 7.2;
const MAX_POINTS = 300;

export default function EntropyChart({ files }: { files: FileScannedEvent[] }) {
  const pts = files.filter((f) => f.scan_status === "COMPLETE").slice(-MAX_POINTS);
  const plotW = W - PAD.l - PAD.r;
  const plotH = H - PAD.t - PAD.b;
  const y = (v: number) => PAD.t + plotH - (v / 8) * plotH;
  const x = (i: number) =>
    PAD.l + (pts.length <= 1 ? plotW / 2 : (i / (pts.length - 1)) * plotW);

  return (
    <section className="rounded-lg border border-line bg-card p-4">
      <div className="mb-2 flex items-baseline justify-between">
        <h2 className="text-sm font-medium text-slate-200">Shannon entropy per file</h2>
        <span className="text-xs text-slate-500">threshold {THRESHOLD} bits/byte</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img"
        aria-label="Scatter plot of file entropy, 0 to 8, with a threshold line at 7.2">
        {[0, 2, 4, 6, 8].map((t) => (
          <g key={t}>
            <line x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} stroke="#1e293b" strokeWidth={1} />
            <text x={PAD.l - 6} y={y(t) + 3} textAnchor="end" fontSize={10} fill="#64748b">{t}</text>
          </g>
        ))}
        <line x1={PAD.l} x2={W - PAD.r} y1={y(THRESHOLD)} y2={y(THRESHOLD)} stroke="#ef4444"
          strokeWidth={1.2} strokeDasharray="5 4" />
        <text x={W - PAD.r - 2} y={y(THRESHOLD) - 4} textAnchor="end" fontSize={10} fill="#ef4444">7.2</text>
        {pts.map((f, i) => (
          <circle key={f.event_id} cx={x(i)} cy={y(f.entropy)} r={4.5} fill={TIER_HEX[f.tier]}
            fillOpacity={0.85} stroke="#0b0f19" strokeWidth={1}>
            <title>{`${f.filename} — H=${f.entropy.toFixed(2)} (${f.tier})`}</title>
          </circle>
        ))}
        {pts.length === 0 && (
          <text x={W / 2} y={H / 2} textAnchor="middle" fontSize={12} fill="#64748b">
            Waiting for scan results…
          </text>
        )}
        <text x={PAD.l} y={H - 5} fontSize={10} fill="#64748b">oldest</text>
        <text x={W - PAD.r} y={H - 5} textAnchor="end" fontSize={10} fill="#64748b">newest</text>
      </svg>
    </section>
  );
}
