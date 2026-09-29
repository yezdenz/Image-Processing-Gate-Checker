# Image Processing Gate Checker 🎥🚪

An automated computer vision surveillance system designed to monitor CCTV RTSP streams, detect gate status (Open, Closed, Moving, Obstructed), maintain tamper-resistant audit logs, and trigger alerts.

---

## 📌 Overview

The **Image Processing Gate Checker** connects to local IP camera streams (defaulting to LAN CCTV at `rtsp://192.168.1.4:554/stream1`), ingests high-definition video frames via OpenCV / PyAV, extracts a configurable Region of Interest (ROI) covering the gate boundaries, runs state-classification algorithms, and logs timestamped audit records with visual proof.

### Key Capabilities
- **Resilient RTSP Ingestion**: Reconnection engine with exponential backoff and TCP transport to handle network jitter.
- **ROI & Computer Vision Gate Detection**: Configurable polygonal ROI with adaptive thresholding, background subtraction, and contour edge-density verification.
- **State Machine Transitions**: Distinguishes between `CLOSED`, `OPEN`, `TRANSITIONING`, and `OBSTRUCTED` gate states with hysteresis confirmation to eliminate false triggers.
- **Full Audit Logging**: Structured JSONL audit trails with masked credentials and cryptographic frame hashes.
- **VLC Integration**: Direct invocation and verification through VLC Media Player (`C:\Program Files\VideoLAN\VLC\vlc.exe`).
- **Alerting & Webhooks**: Optional webhooks and notifications on abnormal gate behavior or camera disconnects.

---

## 🏗️ Architecture Summary

```mermaid
flowchart LR
    A["CCTV Camera<br/>192.168.1.4:554"] -->|RTSP / TCP| B["RTSP Stream Ingest"]
    B --> C["Frame Preprocessor<br/>(Resize, Blur, CLAHE)"]
    C --> D["ROI Mask & Gate Detector"]
    D --> E{"State Machine<br/>(Closed / Open / Obstructed)"}
    E -->|State Change| F["Audit Logger<br/>(JSONL & Snapshot)"]
    E -->|Trigger| G["Alert Dispatcher"]
    B -.->|Verification| H["VLC Media Player"]
```

For complete technical specifications, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 📋 System Requirements

- **Operating System**: Windows 10/11, Linux, or macOS
- **Python**: 3.10 or higher
- **Media Player**: [VLC Media Player](https://www.videolan.org/vlc/) (installed at `C:\Program Files\VideoLAN\VLC\vlc.exe`)
- **Network**: Direct LAN access to the camera IP (`192.168.1.4`) on RTSP port `554`

---

## 🚀 Quick Start

### 1. Clone & Set Up Virtual Environment

```powershell
# Clone the repository
git clone https://github.com/your-username/image-processing-gate-checker.git
cd "image-processing-gate-checker"

# Create a Python virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the template configuration files and configure your local settings:

```powershell
cp .env.example .env
cp config.example.yaml config.yaml
```

Edit `.env` to verify your camera endpoint:
```env
CCTV_RTSP_URL=rtsp://192.168.1.4:554/stream1
CCTV_RTSP_TRANSPORT=tcp
VLC_PATH="C:\Program Files\VideoLAN\VLC\vlc.exe"
```

### 3. Verify CCTV Stream via VLC

Test the camera connection directly from PowerShell using VLC:

```powershell
& "C:\Program Files\VideoLAN\VLC\vlc.exe" "rtsp://192.168.1.4/stream1"
```

If the stream requires authentication:
```powershell
& "C:\Program Files\VideoLAN\VLC\vlc.exe" "rtsp://<username>:<password>@192.168.1.4:554/stream1"
```

---

## 📂 Repository Structure

```text
Image Processing Gate Checker/
├── .gitignore               # Ignored files (media, credentials, environments)
├── .env.example             # Environment variables template
├── config.example.yaml      # Vision & detection configuration schema
├── README.md                # Project documentation and guide
├── ARCHITECTURE.md          # Technical architecture & pipeline diagrams
├── AGENTS.md                # AI agent instructions, roles & workflows
├── CHANGELOG.md             # Semantic versioning and changelog
├── AUDIT_LOG.md             # Audit log schema, security & privacy rules
├── CONTRIBUTING.md          # Contribution standards & pull request checklist
├── requirements.txt         # Core Python dependencies
├── src/                     # Application source code
│   ├── __init__.py
│   ├── config.py            # Settings loader & validator
│   ├── stream/              # RTSP ingestion & reconnection manager
│   ├── vision/              # Image processing, ROI extraction & detectors
│   ├── state/               # Gate state machine & hysteresis filters
│   ├── audit/               # Audit logger & snapshot recorder
│   └── main.py              # CLI & service entry point
├── tests/                   # Automated unit & integration tests
│   ├── test_stream.py
│   ├── test_detector.py
│   └── test_state_machine.py
└── scripts/                 # Utility scripts (VLC launcher, calibration)
    ├── launch_vlc.ps1
    └── calibrate_roi.py
```

---

## 🔒 Security & Privacy

- **Never commit `.env` or credentials**: Passwords and camera access tokens must remain strictly local.
- **Credential Masking**: All logs and audit traces sanitize connection strings (`rtsp://***:***@host:port/path`).
- **Retention Controls**: Snapshot evidence and audit logs adhere to retention policies outlined in [AUDIT_LOG.md](AUDIT_LOG.md).

---

## 📄 License & Governance

Refer to [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines and [AGENTS.md](AGENTS.md) for AI pairing protocols.
