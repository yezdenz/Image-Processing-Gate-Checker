# Machine Learning & Model Training Guide 🧠🚪

This document outlines the machine learning architecture, dataset management, training protocols, and evaluation standards for the **Image Processing Gate Checker** vision models.

---

## 1. Problem Formulation & Classes

The gate status classification task is framed as a **supervised multiclass image classification** problem on cropped Region of Interest (ROI) frames extracted from the CCTV stream (`rtsp://192.168.1.4:554/stream1`).

| Class ID | Class Label | Description | Operational Significance |
| :--- | :--- | :--- | :--- |
| `0` | **`CLOSED`** | Gate is fully shut, latched, and stationary. | Normal secure state. |
| `1` | **`OPEN`** | Gate is opened or retracted beyond the threshold. | Access granted / transit in progress. |
| `2` | **`OBSTRUCTED`** | Gate path is blocked by a vehicle, person, or obstacle. | Hazard / security alarm trigger. |

---

## 2. Dataset Architecture & Directory Structure

```text
data/
├── raw/                      # Unprocessed full-frame captures from RTSP (1920x1080 / 1280x720)
├── annotations/              # CSV / JSON labels with frame timestamps & conditions
├── splits/                   # Manifest files for reproducible splits (train.txt, val.txt, test.txt)
└── processed/                # Pre-cropped, standardized ROI patches (224x224 RGB)
    ├── train/
    │   ├── closed/
    │   ├── open/
    │   └── obstructed/
    ├── val/
    │   ├── closed/
    │   ├── open/
    │   └── obstructed/
    └── test/
        ├── closed/
        ├── open/
        └── obstructed/
```

---

## 3. Critical ML Engineering Best Practices

> [!IMPORTANT]
> **Strict Featurization & Preprocessing Ordering**:
> Always partition the dataset into training, validation, and test splits **BEFORE** computing any dataset statistics, normalizations, or fitting encoders. Never allow information from the validation or test sets to leak into the training transformation pipeline.

### 3.1 Chronological / Session-Based Splitting (No Random Shuffling)
- Video frames captured in temporal proximity exhibit extreme mutual information (>95% frame-to-frame correlation).
- **Rule**: Do **NOT** use naive random train/val/test splits. Instead, partition data by **recording sessions / days / distinct time blocks**:
  - **Train Set (70%)**: Sessions from Days 1–5 (morning, afternoon, night IR).
  - **Validation Set (15%)**: Session from Day 6 (distinct weather and illumination conditions).
  - **Test Set (15%)**: Session from Day 7 (unseen lighting, rain/sun conditions).

### 3.2 Handling Severe Class Imbalance
In access control environments, physical gates typically remain in the `CLOSED` state for ~90–95% of the day:
- **Class-Weighted Cross-Entropy**: Apply inverse-frequency class weights:
  $$\mathcal{W}_c = \frac{N_{total}}{K \cdot N_c}$$
- **Focal Loss**: Focus gradient updates on hard, ambiguous examples (e.g., partial gate ajar or shadows mimicking obstacles).
- **Data Augmentation**: Apply color jitter, Gaussian noise, perspective warp, and simulated lighting transitions to underrepresented `OPEN` and `OBSTRUCTED` classes.

---

## 4. Model Architectures & Selection

```mermaid
flowchart LR
    A["Raw Frame (CCTV)"] --> B["ROI Extraction (Crop 224x224)"]
    B --> C["Preprocessing & CLAHE"]
    C --> D{"Backbone Architecture"}
    D -->|Baseline (Fast)| E["GateNet-Lite (Custom 4-layer CNN)"]
    D -->|Production (Optimal)| F["MobileNetV3-Small / ShuffleNetV2"]
    D -->|High-Accuracy (Server)| G["ResNet-18 / EfficientNet-B0"]
    E --> H["Softmax Head (3 Classes)"]
    F --> H
    G --> H
    H --> I["Argmax + Confidence Score"]
```

### 4.1 Production Model: MobileNetV3-Small
- **Parameters**: ~1.5M parameters (lightweight, minimal memory footprint).
- **Latency Budget**: $< 12 \text{ ms}$ on standard x86 CPU without requiring dedicated GPU acceleration.
- **Transfer Learning**: Pretrained on ImageNet, frozen early feature extractor, fine-tuning final convolutional blocks and linear classification head.

---

## 5. Training & Evaluation Protocol

### 5.1 Training Hyperparameters
- **Optimizer**: AdamW ($\beta_1 = 0.9, \beta_2 = 0.999$, weight decay $= 10^{-4}$)
- **Learning Rate**: $1 \times 10^{-3}$ with cosine annealing scheduler down to $1 \times 10^{-5}$
- **Batch Size**: 32
- **Epochs**: 30 (with EarlyStopping patience = 5 on validation Macro F1)

### 5.2 Evaluation Metrics
- **Macro F1-Score**: Primary metric ensuring equal importance across rare classes (`OBSTRUCTED`).
- **Confusion Matrix**: Critical for verifying False Negative rates (missing an open or obstructed gate carries higher risk than a false alarm).
- **Inference Latency**: Benchmarked using ONNX Runtime with 100 warmup iterations and 1,000 timed inferences.

---

## 6. End-to-End Workflow

### Step 1: Collect Raw CCTV Frames
Run the dataset collection tool to record frames at periodic intervals:
```powershell
python scripts/capture_dataset.py --interval 5 --output data/raw/
```

### Step 2: Crop & Annotate ROIs
Process raw captures into normalized 224x224 crops using the gate boundary polygon:
```powershell
python training/prepare_dataset.py --input data/raw/ --output data/processed/
```

### Step 3: Train the Model
```powershell
python training/train.py --config training/config.yaml
```

### Step 4: Evaluate & Generate Performance Report
```powershell
python training/evaluate.py --checkpoint models/checkpoints/best_gate_model.pt
```

### Step 5: Export to ONNX for Production Inference
```powershell
python training/export_onnx.py --checkpoint models/checkpoints/best_gate_model.pt --output models/exported/gate_classifier.onnx
```
