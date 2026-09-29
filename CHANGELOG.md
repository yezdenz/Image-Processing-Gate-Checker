# Changelog

All notable changes to the **Image Processing Gate Checker** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Full Python OpenCV pipeline implementation (`src/`).
- Real-time GUI / CLI dashboard for monitoring gate status.
- Webhook dispatcher for external integration (Slack, Discord, Home Assistant, Telegram).
- Interactive ROI calibration tool (`scripts/calibrate_roi.py`).

## [0.2.0] - 2026-09-29

### Added
- **Machine Learning & Model Training Infrastructure**:
  - `MODEL_TRAINING.md` defining dataset partitioning (chronological session splits), class imbalance mitigation, and MobileNetV3 edge architecture.
  - Standardized dataset directory hierarchy (`data/raw/`, `data/processed/train|val|test/`, `data/annotations/`, `models/checkpoints/`, `models/exported/`).
  - Automated frame collector (`scripts/capture_dataset.py`) for streaming directly from RTSP into raw dataset.
  - Modular PyTorch training pipeline:
    - `training/dataset.py`: Image transforms, normalization, and inverse-frequency class weights calculation.
    - `training/model.py`: Custom `GateNetLite` and fine-tuned `MobileNetV3-Small`.
    - `training/train.py`: Full training loop with AdamW, Cosine Annealing, validation loop, and best checkpoint saving.
    - `training/evaluate.py`: Confusion matrix, per-class F1/precision/recall, and inference latency benchmark.
    - `training/export_onnx.py`: Production export to ONNX runtime format.
    - `training/prepare_dataset.py`: Automated ROI patch extraction and cropping.
  - Deep learning dependencies added to `requirements.txt` (`torch`, `torchvision`, `scikit-learn`, `onnx`, `onnxruntime`, `matplotlib`).
- **Stream Authentication**:
  - Secure `.env` configuration for local camera credentials.
  - Updated `scripts/launch_vlc.ps1` with automated credential ingestion and URL sanitization.

---

## [0.1.0] - 2026-09-29

### Added
- **Project Foundation & Governance**:
  - Comprehensive GitHub repository structure initialized.
  - `.gitignore` rules for Python bytecode, virtual environments, local credentials, CCTV video/image dumps, and audit databases.
  - Environment templates (`.env.example` and `config.example.yaml`) pre-configured for LAN CCTV stream at `rtsp://192.168.1.4:554/stream1`.
- **Documentation Suite**:
  - `README.md` with system overview, architecture flowchart, VLC verification steps, and quick start guide.
  - `ARCHITECTURE.md` detailing the RTSP ingestion engine, vision processing pipeline, hysteresis finite state machine, and sequence diagrams.
  - `AGENTS.md` outlining multi-agent roles, operational constraints, coding standards, and testing procedures.
  - `AUDIT_LOG.md` defining audit logging standards, schema specifications, credential protection policies, and initial connectivity verification records.
  - `CONTRIBUTING.md` defining code quality standards, git workflow, and pull request checklist.
- **Hardware & Stream Verification**:
  - Network and port connectivity test verified against LAN CCTV camera (`192.168.1.4:554` RTSP TCP handshake succeeded).
  - VLC Media Player installation detected and verified at `C:\Program Files\VideoLAN\VLC\vlc.exe`.
