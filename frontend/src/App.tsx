import { useEffect } from "react";
import EntropyChart from "./components/EntropyChart";
import HeaderStatus from "./components/HeaderStatus";
import ScanQueueFeed from "./components/ScanQueueFeed";
import ThreatCounters from "./components/ThreatCounters";
import ThreatLogTable from "./components/ThreatLogTable";
import { useAegisSocket } from "./hooks/useAegisSocket";

export default function App() {
  const { state, dismissToast, dismissAlert } = useAegisSocket();
  const { toast, alert } = state;

  useEffect(() => {
    if (!toast) return;
    const t = window.setTimeout(dismissToast, 6000);
    return () => window.clearTimeout(t);
  }, [toast, dismissToast]);

  useEffect(() => {
    if (!alert) return;
    const t = window.setTimeout(dismissAlert, 3000);
    return () => window.clearTimeout(t);
  }, [alert, dismissAlert]);

  return (
    <div className="min-h-screen">
      {alert && (
        <div role="alert" key={alert.id}
          className="aegis-flash fixed inset-x-0 top-0 z-50 bg-critical px-4 py-2 text-center text-sm font-semibold text-white">
          CRITICAL: {alert.filename}
        </div>
      )}
      <HeaderStatus connected={state.connected} drives={Object.values(state.drives)} />
      <main className="mx-auto max-w-7xl space-y-4 px-4 py-4">
        <ThreatCounters stats={state.stats} />
        <div className="grid gap-4 lg:grid-cols-2">
          <EntropyChart files={state.files} />
          <ScanQueueFeed lines={state.feed} />
        </div>
        <ThreatLogTable files={state.files} />
      </main>
      {toast && (
        <div role="status" key={toast.id} onClick={dismissToast}
          className="fixed bottom-4 right-4 z-50 max-w-sm cursor-pointer rounded-lg border border-live/50 bg-card px-4 py-3 text-sm text-slate-100 shadow-xl">
          {toast.text}
        </div>
      )}
    </div>
  );
}
