// Mirrors backend/app/api/schemas.py field-for-field (checked by qa_demo/test_api.py).

export type Tier = "SAFE" | "SUSPICIOUS" | "CRITICAL";

export interface Stats {
  total: number;
  safe: number;
  suspicious: number;
  critical: number;
  scans_completed: number;
}

export interface DriveState {
  drive: string;
  label: string;
  fs_type: string;
  total_bytes: number;
  simulated: boolean;
  scan_id: string;
  scanning: boolean;
  files_discovered: number;
  files_scanned: number;
  files_skipped: number;
}

export interface UsbConnectedEvent {
  event_id: string;
  timestamp: string;
  type: "USB_CONNECTED";
  scan_id: string;
  drive: string;
  label: string;
  fs_type: string;
  total_bytes: number;
  simulated: boolean;
}

export interface UsbDisconnectedEvent {
  event_id: string;
  timestamp: string;
  type: "USB_DISCONNECTED";
  drive: string;
}

export interface ScanProgressEvent {
  event_id: string;
  timestamp: string;
  type: "SCAN_PROGRESS";
  scan_id: string;
  drive: string;
  files_discovered: number;
  files_scanned: number;
  files_skipped: number;
}

export interface FileScannedEvent {
  event_id: string;
  timestamp: string;
  type: "FILE_SCANNED";
  scan_id: string;
  drive: string;
  file: string;
  filename: string;
  size_bytes: number;
  sha256: string | null;
  md5_legacy: string | null;
  sha1_legacy: string | null;
  entropy: number;
  chi_square: number;
  entropy_exempt: boolean;
  magic_type: string;
  magic_hex: string;
  extension_mismatch: boolean;
  double_extension: boolean;
  rtlo: boolean;
  xor_key: number | null;
  yara_matches: string[];
  authenticode: string;
  likelihood: number;
  impact: number;
  risk_score: number;
  tier: Tier;
  mitre: string[];
  reasons: string[];
  scan_status: "COMPLETE" | "PARTIAL";
  chain_index: number | null;
  chain_hash: string | null;
}

export interface ScanCompleteEvent {
  event_id: string;
  timestamp: string;
  type: "SCAN_COMPLETE";
  scan_id: string;
  drive: string;
  total: number;
  safe: number;
  suspicious: number;
  critical: number;
  duration_s: number;
  cancelled: boolean;
}

export interface AuditStatusEvent {
  event_id: string;
  timestamp: string;
  type: "AUDIT_STATUS";
  valid: boolean;
  length: number;
  broken_at: number | null;
}

export interface HeartbeatEvent {
  event_id: string;
  timestamp: string;
  type: "HEARTBEAT";
  clients: number;
}

export interface SnapshotEvent {
  event_id: string;
  timestamp: string;
  type: "SNAPSHOT";
  events: Record<string, unknown>[];
  stats: Stats;
  drives: DriveState[];
}

export type TelemetryEvent =
  | UsbConnectedEvent
  | UsbDisconnectedEvent
  | ScanProgressEvent
  | FileScannedEvent
  | ScanCompleteEvent
  | AuditStatusEvent
  | HeartbeatEvent
  | SnapshotEvent;

export interface HealthResponse {
  status: string;
  yara_rules: number;
  intel_providers_online: string[];
  ws_clients: number;
}

export interface SimulateResponse {
  scan_id: string;
  drive: string;
}

export interface EjectResponse {
  ejected: boolean;
}
