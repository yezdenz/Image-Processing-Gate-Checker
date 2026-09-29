# Security, System & Operations Audit Log

This document provides the operational audit policies, schema definitions, security compliance rules, and historical audit records for the **Image Processing Gate Checker**.

---

## 1. Audit Logging Policy

The **Image Processing Gate Checker** monitors physical access control infrastructure. As such, maintaining verifiable, tamper-evident records of system operation, state changes, and operator actions is critical.

### 1.1 Core Audit Rules
1. **Append-Only Logging**: Audit logs (`audit_events.jsonl`) are strictly append-only. No existing records may be modified or deleted programmatically.
2. **Credential Sanitization**: Passwords, RTSP tokens, and sensitive network credentials MUST be stripped or replaced with `***` before writing to any log destination.
3. **Cryptographic Integrity**: Whenever a physical gate state transition occurs (e.g., `CLOSED` -> `OPEN` or `OBSTRUCTED`), a snapshot frame is saved to disk and its cryptographic hash (SHA-256) is recorded directly in the audit log entry.
4. **Time Synchronization**: All audit timestamps must record ISO 8601 UTC time (`timestamp_utc`) alongside local host time (`timestamp_local`) to avoid ambiguity across timezones or daylight saving changes.

---

## 2. Audit Event Schema Specification

All runtime audit events conform to the following JSON schema:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GateCheckerAuditEvent",
  "type": "object",
  "required": [
    "event_id",
    "timestamp_utc",
    "timestamp_local",
    "event_type",
    "severity",
    "camera_id",
    "source_stream_masked"
  ],
  "properties": {
    "event_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this audit event."
    },
    "timestamp_utc": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC timestamp."
    },
    "timestamp_local": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 local host timestamp with timezone offset."
    },
    "event_type": {
      "type": "string",
      "enum": [
        "SYSTEM_INITIALIZATION",
        "CAMERA_CONNECTION_ESTABLISHED",
        "CAMERA_DISCONNECTED",
        "CAMERA_RECONNECT_ATTEMPT",
        "GATE_STATE_TRANSITION",
        "GATE_OBSTRUCTION_DETECTED",
        "SECURITY_ALERT_TRIGGERED",
        "CONFIGURATION_MODIFIED",
        "MANUAL_OVERRIDE"
      ]
    },
    "severity": {
      "type": "string",
      "enum": ["INFO", "WARNING", "ERROR", "CRITICAL"]
    },
    "camera_id": {
      "type": "string",
      "description": "Configured identifier for the CCTV camera."
    },
    "source_stream_masked": {
      "type": "string",
      "description": "RTSP URL with credentials masked, e.g. rtsp://***:***@192.168.1.4:554/stream1"
    },
    "details": {
      "type": "object",
      "properties": {
        "previous_state": { "type": "string" },
        "current_state": { "type": "string" },
        "confidence": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
        "snapshot_path": { "type": "string" },
        "snapshot_sha256": { "type": "string" },
        "message": { "type": "string" }
      }
    }
  }
}
```

---

## 3. Privacy, Data Governance & Compliance

1. **Storage Retention**:
   - High-resolution video buffers are processed in memory and not permanently recorded unless a critical incident or obstruction occurs.
   - Audit snapshots captured on state change are retained for **30 days** by default before archival or automated rotation.
   - Structured JSONL audit trails are archived monthly and retained according to local facility compliance regulations.
2. **Surveillance Privacy**:
   - The Region of Interest (ROI) is masked strictly to the gate boundary, preventing incidental capture or processing of adjacent public sidewalks or private neighboring property.

---

## 4. Historical System Audit Records

### Log Entry: AUD-20260929-001
- **Timestamp (UTC)**: `2026-09-29T05:20:17Z`
- **Timestamp (Local)**: `2026-09-29T13:20:17+08:00`
- **Action Type**: Hardware Discovery & Network Probing
- **Target Host**: `192.168.1.4`
- **Subsystem**: LAN Connectivity & Port Prober
- **Result**: `SUCCESS`
- **Details**:
  - ICMP Ping to `192.168.1.4` succeeded (`True`).
  - TCP handshake on RTSP Port `554` confirmed open (`TcpTestSucceeded: True`).
  - Local host interface: `Ethernet` (`192.168.1.2` -> `192.168.1.4:554`).
  - VLC Media Player binary verified at `C:\Program Files\VideoLAN\VLC\vlc.exe`.

### Log Entry: AUD-20260929-002
- **Timestamp (UTC)**: `2026-09-29T05:26:00Z`
- **Timestamp (Local)**: `2026-09-29T13:26:00+08:00`
- **Action Type**: Repository Initialization & Governance Baseline
- **Subsystem**: Documentation & Configuration Engine
- **Result**: `SUCCESS`
- **Details**:
  - Baseline documentation suite established (`README.md`, `ARCHITECTURE.md`, `AGENTS.md`, `CHANGELOG.md`, `AUDIT_LOG.md`, `CONTRIBUTING.md`).
  - Security configuration created: `.gitignore` and template environments (`.env.example`, `config.example.yaml`).
  - Camera credentials and local IPs protected from accidental public commit.

### Log Entry: AUD-20260929-003
- **Timestamp (UTC)**: `2026-09-29T05:30:00Z`
- **Timestamp (Local)**: `2026-09-29T13:30:00+08:00`
- **Action Type**: CCTV Stream Authentication & Machine Learning Pipeline Preparation
- **Subsystem**: Stream Ingest & Model Training
- **Result**: `SUCCESS`
- **Details**:
  - Authenticated CCTV credentials safely provisioned to `.env` (strictly masked in all logs and audits: `rtsp://***:***@192.168.1.4:554/stream1`).
  - `scripts/launch_vlc.ps1` updated with automated `.env` credential extraction and low-latency TCP transport; launched successfully.
  - Model training directories initialized (`data/raw/`, `data/processed/`, `data/annotations/`, `models/checkpoints/`, `models/exported/`).
  - Model training governance established in [MODEL_TRAINING.md](MODEL_TRAINING.md) adhering to `ml-best-practices` (chronological session splitting, class-weighted loss, MobileNetV3 backbone, ONNX export).
  - Training scripts provided: `scripts/capture_dataset.py`, `training/dataset.py`, `training/model.py`, `training/train.py`, `training/evaluate.py`, `training/export_onnx.py`.
