# AI Agent Guidelines & Operating Protocols

This document defines the roles, operational constraints, pairing conventions, and coding standards for AI coding agents (including Antigravity, subagents, and automated assistants) working within the **Image Processing Gate Checker** repository.

---

## 1. Core Operating Principles

1. **Security & Zero Credential Exposure**:
   - Never output or commit real passwords, RTSP URLs with credentials, or private access tokens.
   - Always sanitize URLs before logging: replace `rtsp://user:pass@host` with `rtsp://***:***@host`.
   - Never remove or bypass `.gitignore` entries protecting `.env` and `secrets.yaml`.

2. **Hardware & Network Awareness**:
   - The CCTV camera is situated at `rtsp://192.168.1.4:554/stream1` on the local network.
   - Do not bombard the camera with aggressive or rapid-fire connection attempts. Always use backoff intervals (minimum 5s).
   - Recognize that automated CI environments may lack physical camera connectivity; write robust mocks and synthetic frame generators for unit and integration testing.

3. **Deterministic & Resilient Code**:
   - Use strict type annotations (`mypy`-compliant) and explicit docstrings.
   - Video processing loops must run defensively: always check if frames are empty or corrupted (`ret == False`).
   - Implement graceful shutdown handlers (`signal.SIGINT`, `signal.SIGTERM`) to release camera streams and close file handles.

---

## 2. Specialized Agent Roles

When decomposing tasks or running parallel workstreams, adopt the following specialized roles:

```mermaid
flowchart TD
    LEAD["Lead Orchestrator Agent<br/>(Task Planning, Scope & Governance)"]
    VISION["Vision & Algorithm Agent<br/>(OpenCV, ROI, CLAHE, Detection Logic)"]
    INFRA["Streaming & Ingest Agent<br/>(RTSP, Reconnection, Watchdogs, VLC)"]
    AUDIT["Audit & Security Agent<br/>(Audit Trails, Hashing, Log Formatting)"]
    QA["QA & Verification Agent<br/>(Mocks, Pytest, Synthetic Feeds)"]
    COMMIT["Auto-Commit Agent<br/>(Atomic Git Commits & Conventional Diffs)"]

    LEAD --> VISION
    LEAD --> INFRA
    LEAD --> AUDIT
    LEAD --> QA
    LEAD --> COMMIT
```

### 2.1 Streaming & Ingestion Agent
- **Responsibilities**:
  - Managing RTSP connections (`cv2.VideoCapture`, `ffmpeg`, `pyav`).
  - Handling network disconnections, packet jitter, and watchdog health checks.
  - Ensuring TCP transport flags (`-rtsp_transport tcp`) are properly set.
- **Rules**:
  - Never allow an infinite blocking call when opening a stream. Use timeouts and async or threaded capture loops.

### 2.2 Vision & Algorithm Agent
- **Responsibilities**:
  - Constructing ROI masks (polygonal and rectangular).
  - Preprocessing (resizing, grayscale conversion, CLAHE equalization, Gaussian smoothing).
  - Background subtraction and contour analysis for gate state classification.
- **Rules**:
  - Ensure processing logic is modularized and accepts NumPy arrays (`np.ndarray`) as inputs.
  - Do not hardcode fixed pixel coordinates; support normalized coordinates `[0.0 - 1.0]` relative to frame resolution.

### 2.3 Audit & Security Agent
- **Responsibilities**:
  - Maintaining [AUDIT_LOG.md](AUDIT_LOG.md) and structured JSONL logging.
  - Generating cryptographic hashes (SHA-256) for audit snapshots.
  - Sanitizing sensitive camera endpoints and maintaining compliance documentation.

### 2.4 QA & Verification Agent
- **Responsibilities**:
  - Creating mock video streams (e.g., generating synthetic colored frames with simulated gate opening/closing).
  - Writing automated `pytest` test suites that can run in headless CI without a physical camera.
  - Benchmarking frame throughput (FPS) and memory leakage.

### 2.5 Auto-Commit Agent
- **Responsibilities**:
  - Inspecting git staging status and identifying changed or untracked artifacts.
  - Decomposing repository changes into atomic, single-item commits.
  - Generating rich Conventional Commit titles (`feat`, `fix`, `docs`, `chore`, `test`) and descriptive bodies explaining the rationale and technical impact of each item.
  - Guarding against the accidental commit of `.env`, camera credentials, or temporary video dumps.
- **Rules**:
  - Commit items one by one (`git add <file>`, `git commit -m "<msg>"`).
  - Never squash disparate features into a single generic commit.
  - Run `python scripts/auto_commit.py` or invoke the `auto_commit_agent` subagent.

---

## 3. Development Workflow & Tool Protocols

### 3.1 Environment & Execution
- **OS**: Windows (PowerShell shell).
- **VLC Path**: `C:\Program Files\VideoLAN\VLC\vlc.exe`.
- **Python**: Always operate inside the virtual environment (`.venv`).
- **Command Guidelines**:
  - Use non-blocking commands when starting video monitors or VLC.
  - In PowerShell, invoke VLC using:
    ```powershell
    & "C:\Program Files\VideoLAN\VLC\vlc.exe" "rtsp://192.168.1.4/stream1"
    ```

### 3.2 Testing Protocol
1. **Mock Verification**: Run `pytest tests/` ensuring all tests pass without network dependencies.
2. **Camera Health Ping**: Test LAN connectivity to camera (`Test-NetConnection -ComputerName 192.168.1.4 -Port 554`).
3. **Audit Log Verification**: Confirm that state transitions append valid JSONL records matching the schema defined in [AUDIT_LOG.md](AUDIT_LOG.md).

---

## 4. Code Standards & Style Guide

- **Language**: Python 3.10+
- **Formatting**: PEP 8 standards, 4-space indentation, max line length 100 characters.
- **Type Hints**: Mandatory for all function signatures.
  ```python
  def process_frame(frame: np.ndarray, roi_polygon: list[tuple[float, float]]) -> tuple[str, float]:
      """Process a single frame and return the detected gate state and confidence.
      
      Args:
          frame: BGR image array from the video stream.
          roi_polygon: Normalized vertices of the gate region.
          
      Returns:
          Tuple of (state_name, confidence_score).
      """
  ```
- **Error Handling**: Use specific exception classes (`CameraConnectionError`, `InvalidFrameError`, `ConfigurationError`). Avoid bare `except:`.

---

## 5. Changelog & Commit Etiquette

- Agents must update [CHANGELOG.md](CHANGELOG.md) whenever new features, bug fixes, or structural changes are committed.
- Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:
  - `feat(vision): add adaptive thresholding for nighttime gate detection`
  - `fix(stream): implement reconnect exponential backoff`
  - `docs(agents): update testing guidelines and VLC procedures`
