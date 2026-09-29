<#
.SYNOPSIS
    Autonomous Git commit tool that stages and commits repository items one by one.

.DESCRIPTION
    Iterates over uncommitted changes, stages items individually, and applies
    rich Conventional Commit descriptions conforming to AGENTS.md standards.

.EXAMPLE
    .\scripts\auto_commit.ps1
#>

$ErrorActionPreference = "Stop"

$CommitRegistry = @{
    ".gitignore" = @{
        Title = "chore(repo): add comprehensive .gitignore for CCTV media, models, and credentials"
        Body = "Ensures raw video streams, frame dumps, PyTorch/ONNX checkpoints, and local .env files are excluded from source control."
    }
    ".env.example" = @{
        Title = "chore(config): add .env.example environment variables template for RTSP stream"
        Body = "Provides standard configuration variables for LAN CCTV (192.168.1.4:554), transport flags, and local paths."
    }
    "config.example.yaml" = @{
        Title = "chore(config): add config.example.yaml schema for vision pipeline and gate ROI"
        Body = "Defines configuration hierarchy for camera ingestion, CLAHE preprocessing, polygonal ROI vertices, and alert thresholds."
    }
    "requirements.txt" = @{
        Title = "chore(deps): add requirements.txt with OpenCV, PyTorch, ONNX, and quality tools"
        Body = "Specifies dependencies for computer vision, deep learning models, serialization, and test automation."
    }
    "README.md" = @{
        Title = "docs(readme): add system overview, architecture diagram, and quickstart guide"
        Body = "Includes project description, Mermaid data flow flowchart, hardware requirements, and VLC verification procedures."
    }
    "ARCHITECTURE.md" = @{
        Title = "docs(arch): add technical design covering RTSP ingestion, vision pipeline, and FSM"
        Body = "Details system architecture, sequence diagrams, hysteresis state machine, and network failure resilience strategies."
    }
    "AGENTS.md" = @{
        Title = "docs(agents): add AGENTS.md defining AI pairing protocols and subagent governance"
        Body = "Establishes operating rules, specialized agent roles (Vision, Streaming, Audit, QA, Auto-Commit), and strict zero credential exposure policies."
    }
    "AUDIT_LOG.md" = @{
        Title = "docs(audit): add AUDIT_LOG.md with event schemas, privacy policies, and hardware logs"
        Body = "Defines JSON schema for gate state transitions, cryptographic frame hashing rules, and initial hardware connectivity records."
    }
    "CHANGELOG.md" = @{
        Title = "docs(changelog): initialize CHANGELOG.md following Keep a Changelog and SemVer"
        Body = "Establishes version tracking baseline (v0.1.0 project foundation, v0.2.0 ML training infrastructure)."
    }
    "CONTRIBUTING.md" = @{
        Title = "docs(contributing): add contribution standards, branching strategy, and PR checklist"
        Body = "Outlines code style, Conventional Commits formatting, unit testing rules, and PR submission checklist."
    }
    "MODEL_TRAINING.md" = @{
        Title = "docs(ml): add MODEL_TRAINING.md with ML best practices, session splitting, and MobileNetV3 specs"
        Body = "Specifies chronological session-based dataset splitting, class weighting, MobileNetV3 edge architecture, and evaluation metrics."
    }
    "scripts/launch_vlc.ps1" = @{
        Title = "feat(scripts): add launch_vlc.ps1 for low-latency TCP RTSP stream inspection"
        Body = "PowerShell helper script that loads credentials from .env, masks passwords in console output, and launches VLC."
    }
    "scripts/capture_dataset.py" = @{
        Title = "feat(dataset): add capture_dataset.py for periodic and keypress RTSP frame harvesting"
        Body = "Captures raw frames from the CCTV stream at fixed intervals or via spacebar keypress, saving timestamped images to data/raw/."
    }
    "scripts/auto_commit.py" = @{
        Title = "feat(scripts): add auto_commit.py for automated single-item conventional commits"
        Body = "Inspects git staging status, groups or isolates items atomically, and applies rich Conventional Commit messages."
    }
    "scripts/auto_commit.ps1" = @{
        Title = "feat(scripts): add auto_commit.ps1 PowerShell automation for atomic commits"
        Body = "Native PowerShell implementation of the Auto-Commit Agent to stage and commit changed items one by one."
    }
    "data/" = @{
        Title = "chore(dataset): initialize data directory structure for raw, processed, and annotation splits"
        Body = "Creates directory hierarchy with .gitkeep placeholders for raw captures, train/val/test splits, and labels."
    }
    "src/" = @{
        Title = "chore(src): initialize source package directories for stream, vision, state, and audit modules"
        Body = "Establishes clean modular source hierarchy for RTSP streaming, OpenCV image processing, state logic, and audit dispatchers."
    }
    "training/" = @{
        Title = "feat(ml): initialize PyTorch training pipeline with dataset loader, models, and ONNX exporter"
        Body = "Implements modular training scripts: dataset.py (transforms & class weights), model.py (GateNetLite & MobileNetV3), train.py (AdamW & early stopping), evaluate.py (confusion matrix & latency), export_onnx.py, and prepare_dataset.py."
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Auto-Commit Agent: Staging and committing items one by one..." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

$PriorityOrder = @(
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
    "scripts/auto_commit.py",
    "scripts/auto_commit.ps1",
    "data/",
    "src/",
    "training/"
)

$CommittedCount = 0

foreach ($target in $PriorityOrder) {
    # Check if target has uncommitted changes
    $status = git status --porcelain $target
    if ($status) {
        $meta = $CommitRegistry[$target]
        if (-not $meta) {
            $meta = @{
                Title = "feat: update $target"
                Body = "Automated commit for $target."
            }
        }

        # Stage target item
        git add $target

        # Check if anything is staged
        $staged = git diff --cached --name-only
        if ($staged) {
            $msg = "$($meta.Title)`n`n$($meta.Body)"
            git commit -m $msg | Out-Null
            Write-Host "[OK] Committed [$target]: $($meta.Title)" -ForegroundColor Yellow
            $CommittedCount++
        }
    }
}

# Any remaining uncommitted files
$remaining = git status --porcelain
if ($remaining) {
    $lines = $remaining -split "`n"
    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if ($trimmed.Length -ge 4) {
            $file = $trimmed.Substring(3).Trim().Trim('"').Trim("'")
            if ($file -and (Test-Path $file)) {
                git add $file
                $staged = git diff --cached --name-only
                if ($staged) {
                    $title = "feat: add $file"
                    $body = "Track $file in repository."
                    git commit -m "$title`n`n$body" | Out-Null
                    Write-Host "[OK] Committed [$file]: $title" -ForegroundColor Yellow
                    $CommittedCount++
                }
            }
        }
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Finished. Executed $CommittedCount atomic commits successfully." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
