"""
ml_pipeline/train.py
Fine-tuning script for microsoft/codebert-base on the CodeXGLUE Devign Vulnerability Dataset.
Uses robust native PyTorch training loop with AdamW, tqdm live progress bars, and F1 evaluation.

Usage:
    .\\venv\\Scripts\\python ml_pipeline/train.py --epochs 3 --batch_size 8 --lr 2e-5
"""

import os
import sys
import argparse
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader
    import numpy as np
    from tqdm import tqdm
    from transformers import (
        AutoTokenizer,
        AutoModelForSequenceClassification,
        get_linear_schedule_with_warmup
    )
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
    HAS_DEPS = True
except ImportError as e:
    HAS_DEPS = False
    IMPORT_ERROR = str(e)

from ml_pipeline.dataset import DevignCodeDataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "devign"
OUTPUT_DIR = PROJECT_ROOT / "ml_pipeline" / "checkpoints" / "best_model"


def evaluate(model, dataloader, device):
    """Evaluates the model on validation data and returns metrics."""
    model.eval()
    all_preds = []
    all_labels = []
    total_val_loss = 0.0

    criterion = nn.CrossEntropyLoss()

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            loss = criterion(logits, labels)
            total_val_loss += loss.item()

            preds = torch.argmax(logits, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())

    avg_loss = total_val_loss / max(len(dataloader), 1)
    acc = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_labels, all_preds, average='binary', zero_division=0
    )

    return {
        "val_loss": round(avg_loss, 4),
        "accuracy": round(acc, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4)
    }


def main():
    parser = argparse.ArgumentParser(description="Fine-tune CodeBERT for Vulnerability Classification")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs (default: 3)")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size (default: 8)")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate (default: 2e-5)")
    parser.add_argument("--max_length", type=int, default=256, help="Max code token length (default: 256)")
    args = parser.parse_args()

    print("=================================================================")
    print("      Codebase Architecture & Risk Auditor — Model Training       ")
    print("      Fine-Tuning CodeBERT (microsoft/codebert-base, 125M)        ")
    print("=================================================================")

    if not HAS_DEPS:
        print(f"\n[ERROR] Missing required ML libraries: {IMPORT_ERROR}")
        return

    # Check hardware
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n[Hardware Status]")
    print(f"  Target Device: {str(device).upper()}")
    if device.type == "cuda":
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        print(f"  GPU Name: {gpu_name}")
        print(f"  VRAM Available: {vram_gb:.2f} GB")
    else:
        print("  [NOTE] Running on CPU (CUDA not active in this environment).")

    # Check Dataset
    train_path = DATA_DIR / "train.jsonl"
    valid_path = DATA_DIR / "valid.jsonl"

    if not train_path.exists() or not valid_path.exists():
        print(f"\n[ERROR] Dataset not found in {DATA_DIR}.")
        print("Please run: .\\venv\\Scripts\\python ml_pipeline/download_dataset.py")
        return

    # Load Tokenizer & Model
    model_name = "microsoft/codebert-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2,
        use_safetensors=True
    )
    model.to(device)

    # Prepare DataLoaders
    print("\n[Loading Dataset Splits]...")
    train_dataset = DevignCodeDataset(str(train_path), tokenizer=tokenizer, max_length=args.max_length)
    valid_dataset = DevignCodeDataset(str(valid_path), tokenizer=tokenizer, max_length=args.max_length)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    valid_loader = DataLoader(valid_dataset, batch_size=args.batch_size, shuffle=False)

    print(f"  Training Samples: {len(train_dataset)} ({len(train_loader)} batches)")
    print(f"  Validation Samples: {len(valid_dataset)} ({len(valid_loader)} batches)")

    # Optimizer & Scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=max(1, int(total_steps * 0.1)),
        num_training_steps=total_steps
    )
    criterion = nn.CrossEntropyLoss()

    best_f1 = -1.0
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[Starting Training Loop in Terminal]...")
    print("=" * 65)

    start_time = time.time()

    for epoch in range(args.epochs):
        model.train()
        total_train_loss = 0.0

        pbar = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{args.epochs}", unit="batch")
        for batch in pbar:
            optimizer.zero_grad()

            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            loss = criterion(outputs.logits, labels)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()

            total_train_loss += loss.item()
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        avg_train_loss = total_train_loss / max(len(train_loader), 1)

        # Validation at end of epoch
        val_metrics = evaluate(model, valid_loader, device)
        print(f"\n Epoch {epoch + 1} Results:")
        print(f"   Train Loss: {avg_train_loss:.4f} | Val Loss: {val_metrics['val_loss']:.4f}")
        print(f"   Accuracy: {val_metrics['accuracy'] * 100:.2f}% | Precision: {val_metrics['precision']:.4f} | Recall: {val_metrics['recall']:.4f} | F1: {val_metrics['f1']:.4f}")

        # Checkpoint if F1 improved
        if val_metrics["f1"] >= best_f1:
            best_f1 = val_metrics["f1"]
            print(f"   [*] New Best Model! Saving checkpoint to {OUTPUT_DIR}...")
            model.save_pretrained(str(OUTPUT_DIR))
            tokenizer.save_pretrained(str(OUTPUT_DIR))

        print("-" * 65)

    elapsed = time.time() - start_time
    print("\n=================================================================")
    print(f"  [SUCCESS] CodeBERT Fine-Tuning Complete in {elapsed:.1f}s!")
    print(f"  Best Validation F1: {best_f1:.4f}")
    print(f"  Saved Weights: {OUTPUT_DIR}")
    print("=================================================================")


if __name__ == "__main__":
    main()
