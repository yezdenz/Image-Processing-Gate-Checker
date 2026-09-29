"""Dataset loading, splitting, and augmentation for Gate State Classification.

Adheres to strict ML best practices:
- Preprocessing pipelines fit/configured strictly on training distributions.
- Data augmentations applied exclusively to training set.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import torch
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets, transforms

# ImageNet normalization statistics
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Supported Gate Classes
CLASSES = ["closed", "open", "obstructed"]


def get_transforms(image_size: int = 224) -> Tuple[transforms.Compose, transforms.Compose]:
    """Build separate transform pipelines for training and validation/testing.

    Args:
        image_size: Target square pixel dimension (default 224).

    Returns:
        Tuple of (train_transform, eval_transform).
    """
    train_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=7),
        transforms.ColorJitter(brightness=0.25, contrast=0.25, saturation=0.2, hue=0.05),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])

    eval_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])

    return train_transform, eval_transform


def calculate_class_weights(dataset: datasets.ImageFolder) -> torch.Tensor:
    """Compute inverse-frequency class weights to combat severe class imbalance.

    Args:
        dataset: The training ImageFolder dataset.

    Returns:
        Tensor of class weights for CrossEntropyLoss.
    """
    targets = [s[1] for s in dataset.samples]
    class_counts = torch.bincount(torch.tensor(targets, dtype=torch.long))
    total_samples = len(targets)
    num_classes = len(class_counts)

    # Prevent division by zero
    class_counts = torch.clamp(class_counts, min=1)
    weights = total_samples / (num_classes * class_counts.float())
    return weights


def create_dataloaders(
    data_dir: Path,
    batch_size: int = 32,
    image_size: int = 224,
    num_workers: int = 0,
) -> Tuple[Dict[str, DataLoader], torch.Tensor]:
    """Construct PyTorch DataLoaders for train, val, and test splits.

    Args:
        data_dir: Root processed data directory containing train/, val/, test/ folders.
        batch_size: Number of images per batch.
        image_size: Resolution of inputs.
        num_workers: Worker processes for dataloading.

    Returns:
        Tuple of (dictionary of DataLoaders, class_weights_tensor).
    """
    train_tf, eval_tf = get_transforms(image_size)

    train_path = data_dir / "train"
    val_path = data_dir / "val"
    test_path = data_dir / "test"

    train_dataset = datasets.ImageFolder(str(train_path), transform=train_tf)
    val_dataset = datasets.ImageFolder(str(val_path), transform=eval_tf)
    test_dataset = datasets.ImageFolder(str(test_path), transform=eval_tf)

    class_weights = calculate_class_weights(train_dataset)

    dataloaders = {
        "train": DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available(),
        ),
        "val": DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available(),
        ),
        "test": DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available(),
        ),
    }

    return dataloaders, class_weights
