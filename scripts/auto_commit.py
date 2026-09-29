"""Auto-Commit Automation Script.

Inspects git status, groups or isolates items atomically, and commits each item
one by one with rich, descriptive Conventional Commit messages.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Mapping of file patterns or paths to descriptive commit metadata
COMMIT_REGISTRY: dict[str, dict[str, str]] = {
    ".gitignore": {
        "title": "chore(repo): add comprehensive .gitignore for CCTV media, models, and credentials",
        "body": "Ensures raw video streams, frame dumps, PyTorch/ONNX checkpoints, and local .env files are excluded from source control.",
    },
    ".env.example": {
        "title": "chore(config): add .env.example environment variables template for RTSP stream",
        "body": "Provides standard configuration variables for LAN CCTV (192.168.1.4:554), transport flags, and local paths.",
    },
    "config.example.yaml": {
        "title": "chore(config): add config.example.yaml schema for vision pipeline and gate ROI",
        "body": "Defines configuration hierarchy for camera ingestion, CLAHE preprocessing, polygonal ROI vertices, and alert thresholds.",
    },
    "requirements.txt": {
        "title": "chore(deps): add requirements.txt with OpenCV, PyTorch, ONNX, and quality tools",
        "body": "Specifies dependencies for computer vision, deep learning models, serialization, and test automation.",
    },
    "README.md": {
        "title": "docs(readme): add system overview, architecture diagram, and quickstart guide",
        "body": "Includes project description, Mermaid data flow flowchart, hardware requirements, and VLC verification procedures.",
    },
    "ARCHITECTURE.md": {
        "title": "docs(arch): add technical design covering RTSP ingestion, vision pipeline, and FSM",
        "body": "Details system architecture, sequence diagrams, hysteresis state machine, and network failure resilience strategies.",
    },
    "AGENTS.md": {
        "title": "docs(agents): add AGENTS.md defining AI pairing protocols and subagent governance",
        "body": "Establishes operating rules, specialized agent roles (Vision, Streaming, Audit, QA), and strict zero credential exposure policies.",
    },
    "AUDIT_LOG.md": {
        "title": "docs(audit): add AUDIT_LOG.md with event schemas, privacy policies, and hardware logs",
        "body": "Defines JSON schema for gate state transitions, cryptographic frame hashing rules, and initial hardware connectivity records.",
    },
    "CHANGELOG.md": {
        "title": "docs(changelog): initialize CHANGELOG.md following Keep a Changelog and SemVer",
        "body": "Establishes version tracking baseline (v0.1.0 project foundation, v0.2.0 ML training infrastructure).",
    },
    "CONTRIBUTING.md": {
        "title": "docs(contributing): add contribution standards, branching strategy, and PR checklist",
        "body": "Outlines code style, Conventional Commits formatting, unit testing rules, and PR submission checklist.",
    },
    "MODEL_TRAINING.md": {
        "title": "docs(ml): add MODEL_TRAINING.md with ML best practices, session splitting, and MobileNetV3 specs",
        "body": "Specifies chronological session-based dataset splitting, class weighting, MobileNetV3 edge architecture, and evaluation metrics.",
    },
    "scripts/launch_vlc.ps1": {
        "title": "feat(scripts): add launch_vlc.ps1 for low-latency TCP RTSP stream inspection",
        "body": "PowerShell helper script that loads credentials from .env, masks passwords in console output, and launches VLC.",
    },
    "scripts/capture_dataset.py": {
        "title": "feat(dataset): add capture_dataset.py for periodic and keypress RTSP frame harvesting",
        "body": "Captures raw frames from the CCTV stream at fixed intervals or via spacebar keypress, saving timestamped images to data/raw/.",
    },
    "data/": {
        "title": "chore(dataset): initialize data directory structure for raw, processed, and annotation splits",
        "body": "Creates directory hierarchy with .gitkeep placeholders for raw captures, train/val/test splits, and labels.",
    },
    "src/": {
        "title": "chore(src): initialize source package directories for stream, vision, state, and audit modules",
        "body": "Establishes clean modular source hierarchy for RTSP streaming, OpenCV image processing, state logic, and audit dispatchers.",
    },
    "training/": {
        "title": "feat(ml): initialize PyTorch training pipeline with dataset loader, models, and ONNX exporter",
        "body": "Implements modular training scripts: dataset.py (transforms & class weights), model.py (GateNetLite & MobileNetV3), train.py (AdamW & early stopping), evaluate.py (confusion matrix & latency), export_onnx.py, and prepare_dataset.py.",
    },
}


def run_git(args: list[str]) -> tuple[int, str]:
    """Execute a git command and return (exit_code, output)."""
    result = subprocess.run(["git"] + args, capture_output=True, text=True, check=False)
    output = (result.stdout + result.stderr).strip()
    return result.returncode, output


def get_uncommitted_items() -> list[str]:
    """List distinct untracked and modified top-level paths."""
    code, out = run_git(["status", "--porcelain"])
    if code != 0 or not out:
        return []

    items = []
    seen = set()
    for line in out.splitlines():
        if len(line) < 4:
            continue
        filepath = line[3:].strip().replace('"', "")
        # Group subdirectories if applicable
        first_segment = filepath.split("/")[0]
        if first_segment in {"data", "src", "training", "scripts"} and filepath.endswith(".gitkeep"):
            target = f"{first_segment}/"
        elif first_segment in {"data", "src"} and not Path(filepath).is_file():
            target = f"{first_segment}/"
        else:
            target = filepath

        if target not in seen:
            seen.add(target)
            items.append(target)
    return items


def commit_item(item: str) -> bool:
    """Stage and commit a specific item with a descriptive Conventional Commit message."""
    meta = COMMIT_REGISTRY.get(item)
    if not meta:
        # Fallback to intelligent default
        clean_name = item.rstrip("/").split("/")[-1]
        meta = {
            "title": f"feat({clean_name}): add or update {item}",
            "body": f"Automated commit tracking updates for {item}.",
        }

    full_message = f"{meta['title']}\n\n{meta['body']}"

    # Stage
    stage_code, stage_out = run_git(["add", item])
    if stage_code != 0:
        print(f"Failed to stage {item}: {stage_out}", file=sys.stderr)
        return False

    # Check if anything is actually staged
    code, out = run_git(["diff", "--cached", "--name-only"])
    if not out.strip():
        print(f"Skipping {item}: Nothing staged.")
        return False

    # Commit
    commit_code, commit_out = run_git(["commit", "-m", full_message])
    if commit_code != 0:
        print(f"Failed to commit {item}: {commit_out}", file=sys.stderr)
        return False

    print(f"[OK] Committed [{item}]: {meta['title']}")
    return True


def auto_commit_all() -> None:
    """Iterate through all uncommitted items and commit each one by one."""
    print("=" * 60)
    print("Auto-Commit Agent: Staging and committing items one by one...")
    print("=" * 60)

    # Priority order for initial setup
    priority_order = [
        ".gitignore",
        ".env.example",
        "config.example.yaml",
        "requirements.txt",
        "README.md",
        "ARCHITECTURE.md",
        "AGENTS.md",
        "AUDIT_LOG.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "MODEL_TRAINING.md",
        "scripts/launch_vlc.ps1",
        "scripts/capture_dataset.py",
        "data/",
        "src/",
        "training/",
    ]

    uncommitted = get_uncommitted_items()
    committed_count = 0

    # Process priority items first
    for target in priority_order:
        matching = [item for item in uncommitted if item == target or item.startswith(target)]
        if matching:
            if commit_item(target):
                committed_count += 1
            uncommitted = [u for u in get_uncommitted_items() if u != target and not u.startswith(target)]

    # Process any remaining items
    for item in uncommitted:
        if commit_item(item):
            committed_count += 1

    print("=" * 60)
    print(f"Finished. Successfully executed {committed_count} atomic commits.")
    print("=" * 60)


if __name__ == "__main__":
    auto_commit_all()
