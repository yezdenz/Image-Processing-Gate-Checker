"""Evaluation and Benchmarking Script for Gate State Classifier.

Computes:
- Per-class Precision, Recall, and F1-score.
- Confusion Matrix.
- Average inference latency on target hardware (CPU).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import classification_report, confusion_matrix

from training.dataset import create_dataloaders
from training.model import get_gate_classifier


def benchmark_latency(model: torch.nn.Module, device: torch.device, input_shape: tuple[int, int, int, int] = (1, 3, 224, 224), iterations: int = 200) -> float:
    """Benchmark inference latency in milliseconds."""
    model.eval()
    dummy_input = torch.randn(*input_shape).to(device)

    # Warmup
    with torch.no_grad():
        for _ in range(20):
            _ = model(dummy_input)

    # Timed run
    start = time.perf_counter()
    with torch.no_grad():
        for _ in range(iterations):
            _ = model(dummy_input)
    end = time.perf_counter()

    avg_ms = ((end - start) / iterations) * 1000.0
    return avg_ms


def evaluate_model(
    checkpoint_path: Path,
    data_dir: Path,
    output_dir: Path,
    batch_size: int = 32,
) -> None:
    """Evaluate checkpoint on the test set."""
    output_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Evaluating checkpoint: {checkpoint_path.name} on {device}")

    checkpoint = torch.load(checkpoint_path, map_location=device)
    backbone = checkpoint.get("backbone", "mobilenet_v3_small")
    class_names = checkpoint.get("class_names", ["closed", "open", "obstructed"])

    # Load model
    model = get_gate_classifier(backbone=backbone, num_classes=len(class_names), pretrained=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    # Dataloaders
    dataloaders, _ = create_dataloaders(data_dir=data_dir, batch_size=batch_size)
    test_loader = dataloaders["test"]

    all_preds: list[int] = []
    all_labels: list[int] = []

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)

            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(labels.cpu().tolist())

    # Classification Metrics
    report = classification_report(
        all_labels,
        all_preds,
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )
    conf_mat = confusion_matrix(all_labels, all_preds)

    # Benchmark latency on CPU
    cpu_device = torch.device("cpu")
    model_cpu = model.to(cpu_device)
    latency_ms = benchmark_latency(model_cpu, cpu_device)

    print("\n" + "=" * 50)
    print("TEST SET EVALUATION REPORT")
    print("=" * 50)
    print(classification_report(all_labels, all_preds, target_names=class_names, zero_division=0))
    print("Confusion Matrix:")
    print(conf_mat)
    print(f"\nAverage CPU Inference Latency: {latency_ms:.2f} ms/frame")
    print("=" * 50)

    # Save results
    results = {
        "checkpoint": str(checkpoint_path),
        "backbone": backbone,
        "classes": class_names,
        "metrics": report,
        "confusion_matrix": conf_mat.tolist(),
        "latency_ms": latency_ms,
    }

    report_file = output_dir / "evaluation_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {report_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Gate State Classifier")
    parser.add_argument("--checkpoint", type=Path, default=Path("models/checkpoints/best_gate_model.pt"), help="Model checkpoint path")
    parser.add_argument("--data-dir", type=Path, default=Path("data/processed"), help="Processed data directory")
    parser.add_argument("--output-dir", type=Path, default=Path("models/eval_results"), help="Directory for output report")
    args = parser.parse_args()

    evaluate_model(checkpoint_path=args.checkpoint, data_dir=args.data_dir, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
