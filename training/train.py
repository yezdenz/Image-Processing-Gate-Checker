"""Training Pipeline for Gate State Classification.

Implements:
- Class-weighted CrossEntropyLoss.
- AdamW optimizer with Cosine Annealing.
- Validation loop tracking Loss, Accuracy, and Macro F1-score.
- Checkpoint persistence for the best validation F1 model.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
from sklearn.metrics import f1_score

from training.dataset import create_dataloaders
from training.model import get_gate_classifier


def train_epoch(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> tuple[float, float]:
    """Execute one training epoch."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for inputs, labels in loader:
        inputs = inputs.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)
        _, preds = torch.max(outputs, 1)
        correct += torch.sum(preds == labels).item()
        total += labels.size(0)

    epoch_loss = running_loss / max(total, 1)
    epoch_acc = correct / max(total, 1)
    return epoch_loss, epoch_acc


def validate_epoch(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float, float]:
    """Evaluate model on the validation set."""
    model.eval()
    running_loss = 0.0
    all_preds: list[int] = []
    all_labels: list[int] = []

    with torch.no_grad():
        for inputs, labels in loader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)

            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(labels.cpu().tolist())

    total = len(all_labels)
    val_loss = running_loss / max(total, 1)
    val_acc = sum(p == l for p, l in zip(all_preds, all_labels)) / max(total, 1)
    val_macro_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)

    return val_loss, val_acc, float(val_macro_f1)


def run_training(
    data_dir: Path,
    output_dir: Path,
    backbone: str = "mobilenet_v3_small",
    epochs: int = 25,
    batch_size: int = 32,
    lr: float = 1e-3,
    patience: int = 5,
) -> None:
    """Run end-to-end model training."""
    output_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device} | Backbone: {backbone}")

    # Build dataloaders
    dataloaders, class_weights = create_dataloaders(data_dir=data_dir, batch_size=batch_size)
    class_weights = class_weights.to(device)

    # Instantiate model
    model = get_gate_classifier(backbone=backbone, num_classes=3, pretrained=True)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    best_val_f1 = 0.0
    patience_counter = 0
    history = []

    best_checkpoint_path = output_dir / "best_gate_model.pt"

    print("=" * 60)
    print(f"{'Epoch':<6} | {'Train Loss':<10} | {'Train Acc':<10} | {'Val Loss':<10} | {'Val Acc':<10} | {'Val F1':<8}")
    print("=" * 60)

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        train_loss, train_acc = train_epoch(model, dataloaders["train"], criterion, optimizer, device)
        val_loss, val_acc, val_f1 = validate_epoch(model, dataloaders["val"], criterion, device)
        scheduler.step()
        elapsed = time.time() - t0

        print(
            f"{epoch:<6} | {train_loss:<10.4f} | {train_acc:<10.2%} | "
            f"{val_loss:<10.4f} | {val_acc:<10.2%} | {val_f1:<8.4f} ({elapsed:.1f}s)"
        )

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "val_loss": val_loss,
            "val_acc": val_acc,
            "val_macro_f1": val_f1,
        })

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            patience_counter = 0
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "backbone": backbone,
                "best_val_f1": best_val_f1,
                "class_names": ["closed", "open", "obstructed"],
            }, best_checkpoint_path)
            print(f" -> Best model saved to {best_checkpoint_path.name} (Macro F1: {best_val_f1:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"\nEarly stopping triggered after {epoch} epochs without improvement.")
                break

    # Save metrics history
    history_path = output_dir / "training_history.json"
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    print(f"Training history saved to {history_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Gate State Classifier")
    parser.add_argument("--data-dir", type=Path, default=Path("data/processed"), help="Path to processed data directory")
    parser.add_argument("--output-dir", type=Path, default=Path("models/checkpoints"), help="Path to save checkpoints")
    parser.add_argument("--backbone", type=str, default="mobilenet_v3_small", choices=["lite", "mobilenet_v3_small", "resnet18"])
    parser.add_argument("--epochs", type=int, default=25, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Initial learning rate")
    parser.add_argument("--patience", type=int, default=5, help="Early stopping patience")
    args = parser.parse_args()

    run_training(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        backbone=args.backbone,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        patience=args.patience,
    )


if __name__ == "__main__":
    main()
