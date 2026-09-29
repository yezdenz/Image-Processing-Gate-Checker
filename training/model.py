"""Neural Network Architectures for Gate Status Classification.

Provides both:
1. GateNetLite: Custom lightweight 4-layer CNN (~250k parameters) for low-power edge CPUs.
2. MobileNetV3-Small / ShuffleNetV2: Transfer-learning backbones for high-accuracy deployments.
"""

from __future__ import annotations

import torch
import torch.nn as nn
from torchvision import models


class GateNetLite(nn.Module):
    """Custom compact CNN designed for ultra-low latency inference on edge CCTV nodes."""

    def __init__(self, num_classes: int = 3, in_channels: int = 3) -> None:
        super().__init__()
        self.features = nn.Sequential(
            # Block 1
            nn.Conv2d(in_channels, 32, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 112x112

            # Block 2
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 56x56

            # Block 3
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 28x28

            # Block 4
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),  # 1x1
        )

        self.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(256, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.2),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x


def get_gate_classifier(
    backbone: str = "mobilenet_v3_small",
    num_classes: int = 3,
    pretrained: bool = True,
) -> nn.Module:
    """Instantiate a gate classifier backbone with custom classification head.

    Args:
        backbone: One of 'lite', 'mobilenet_v3_small', 'shufflenet_v2_x0_5', or 'resnet18'.
        num_classes: Number of target classes (default 3: closed, open, obstructed).
        pretrained: Whether to load ImageNet pre-trained weights.

    Returns:
        Configured PyTorch nn.Module.
    """
    backbone_lower = backbone.lower()

    if backbone_lower == "lite":
        return GateNetLite(num_classes=num_classes)

    elif backbone_lower == "mobilenet_v3_small":
        weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
        model = models.mobilenet_v3_small(weights=weights)
        in_features = model.classifier[0].in_features
        model.classifier = nn.Sequential(
            nn.Linear(in_features, 128),
            nn.Hardswish(inplace=True),
            nn.Dropout(p=0.2),
            nn.Linear(128, num_classes),
        )
        return model

    elif backbone_lower == "shufflenet_v2_x0_5":
        weights = models.ShuffleNet_V2_X0_5_Weights.DEFAULT if pretrained else None
        model = models.shufflenet_v2_x0_5(weights=weights)
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)
        return model

    elif backbone_lower == "resnet18":
        weights = models.ResNet18_Weights.DEFAULT if pretrained else None
        model = models.resnet18(weights=weights)
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)
        return model

    else:
        raise ValueError(f"Unsupported backbone: '{backbone}'. Choose from 'lite', 'mobilenet_v3_small', 'resnet18'.")
