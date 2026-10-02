"""
ml_pipeline/train.py
Fine-tuning script for microsoft/codebert-base on the CodeXGLUE Devign Vulnerability Dataset.
Optimized for local NVIDIA RTX 3050 GPU (4GB-8GB VRAM) using mixed-precision fp16.

Usage:
    python ml_pipeline/train.py --epochs 3 --batch_size 8 --lr 2e-5
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import torch
    import numpy as np
    from transformers import (
        AutoTokenizer,
        AutoModelForSequenceClassification,
        TrainingArguments,
        Trainer,
        DataCollatorWithPadding
    )
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
    HAS_DEPS = True
except ImportError as e:
    HAS_DEPS = False
    IMPORT_ERROR = str(e)

from ml_pipeline.dataset import DevignCodeDataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "devign"
OUTPUT_DIR = PROJECT_ROOT / "ml_pipeline" / "checkpoints"


def compute_metrics(eval_pred):
    """Computes Accuracy, Precision, Recall, and F1 on validation split."""
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='binary', zero_division=0)
    acc = accuracy_score(labels, preds)
    return {
        'accuracy': round(acc, 4),
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'f1': round(f1, 4)
    }


def main():
    parser = argparse.ArgumentParser(description="Fine-tune CodeBERT for Vulnerability Classification")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs (default: 3)")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size per device (default: 8 for RTX 3050)")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate (default: 2e-5)")
    parser.add_argument("--max_length", type=int, default=256, help="Max code token length (default: 256)")
    parser.add_argument("--fp16", action="store_true", default=True, help="Enable mixed precision for GPU acceleration")
    args = parser.parse_args()

    print("=================================================================")
    print("      Codebase Architecture & Risk Auditor — Model Training       ")
    print("      Fine-Tuning CodeBERT (microsoft/codebert-base, 125M)        ")
    print("=================================================================")

    if not HAS_DEPS:
        print(f"\n[ERROR] Missing required ML libraries: {IMPORT_ERROR}")
        print("Please install requirements using:")
        print("  pip install torch transformers datasets scikit-learn numpy accelerate")
        return

    # Check CUDA device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n[Hardware Status]")
    print(f"  Target Device: {device.upper()}")
    if device == "cuda":
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        print(f"  GPU Name: {gpu_name}")
        print(f"  VRAM Available: {vram_gb:.2f} GB (Optimized for RTX 3050)")
    else:
        print("  [NOTE] GPU not detected or CUDA not available. Running on CPU.")
        args.fp16 = False

    # Check Dataset
    train_path = DATA_DIR / "train.jsonl"
    valid_path = DATA_DIR / "valid.jsonl"

    if not train_path.exists() or not valid_path.exists():
        print(f"\n[ERROR] Dataset not found in {DATA_DIR}.")
        print("Please download the Devign dataset first by running:")
        print("  python ml_pipeline/download_dataset.py")
        return

    # Load Tokenizer & Model
    model_name = "microsoft/codebert-base"
    print(f"\n[Loading Pretrained CodeBERT: {model_name}]...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

    # Load Datasets
    print("\n[Loading Dataset Splits]...")
    train_dataset = DevignCodeDataset(str(train_path), tokenizer=tokenizer, max_length=args.max_length)
    valid_dataset = DevignCodeDataset(str(valid_path), tokenizer=tokenizer, max_length=args.max_length)
    print(f"  Training Samples: {len(train_dataset)}")
    print(f"  Validation Samples: {len(valid_dataset)}")

    # Training Arguments
    use_fp16 = args.fp16 and (device == "cuda")
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        warmup_ratio=0.1,
        weight_decay=0.01,
        logging_dir=str(OUTPUT_DIR / "logs"),
        logging_steps=10,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        fp16=use_fp16,
        save_total_limit=2,
        report_to="none"  # Do not require wandb/tensorboard
    )

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics
    )

    # Begin Training
    print("\n[Starting Training Loop in Terminal]...")
    print("=" * 65)
    train_result = trainer.train()

    # Save Best Model
    best_model_path = OUTPUT_DIR / "best_model"
    print(f"\n[Saving Best Model Artifacts to {best_model_path}]...")
    trainer.save_model(str(best_model_path))
    tokenizer.save_pretrained(str(best_model_path))

    # Evaluate on Validation Set
    print("\n[Final Validation Evaluation]...")
    metrics = trainer.evaluate()
    for key, val in metrics.items():
        print(f"  {key}: {val}")

    print("\n=================================================================")
    print("  [SUCCESS] CodeBERT Fine-Tuning Completed Successfully!")
    print(f"  Weights saved in: {best_model_path}")
    print("=================================================================")


if __name__ == "__main__":
    main()
