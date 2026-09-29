"""ONNX Model Exporter for Production Inference.

Exports trained PyTorch weights to an optimized ONNX model suitable for
running inside OpenCV DNN or ONNX Runtime on edge CCTV gateways.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch

from training.model import get_gate_classifier


def export_to_onnx(
    checkpoint_path: Path,
    output_path: Path,
    input_size: int = 224,
    opset_version: int = 17,
) -> None:
    """Export PyTorch checkpoint to ONNX."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    device = torch.device("cpu")

    print(f"Loading checkpoint: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location=device)
    backbone = checkpoint.get("backbone", "mobilenet_v3_small")
    class_names = checkpoint.get("class_names", ["closed", "open", "obstructed"])

    # Instantiate model
    model = get_gate_classifier(backbone=backbone, num_classes=len(class_names), pretrained=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    dummy_input = torch.randn(1, 3, input_size, input_size, requires_grad=False)

    print(f"Exporting to ONNX: {output_path} (opset {opset_version})...")
    torch.onnx.export(
        model,
        dummy_input,
        str(output_path),
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
    )

    print("Verifying exported ONNX model...")
    try:
        import onnx
        onnx_model = onnx.load(str(output_path))
        onnx.checker.check_model(onnx_model)
        print("ONNX model verification succeeded!")
    except ImportError:
        print("Note: 'onnx' package not installed; skipped schema validation.")

    print(f"Export complete: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export PyTorch Gate Classifier to ONNX")
    parser.add_argument("--checkpoint", type=Path, default=Path("models/checkpoints/best_gate_model.pt"), help="PyTorch checkpoint")
    parser.add_argument("--output", type=Path, default=Path("models/exported/gate_classifier.onnx"), help="Target ONNX path")
    parser.add_argument("--size", type=int, default=224, help="Input dimension")
    args = parser.parse_args()

    export_to_onnx(checkpoint_path=args.checkpoint, output_path=args.output, input_size=args.size)


if __name__ == "__main__":
    main()
