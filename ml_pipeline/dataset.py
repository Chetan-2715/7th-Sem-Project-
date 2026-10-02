"""
ml_pipeline/dataset.py
PyTorch Dataset for CodeXGLUE Devign vulnerability classification.
Handles tokenization and sequence padding for microsoft/codebert-base.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import torch
    from torch.utils.data import Dataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    Dataset = object


class DevignCodeDataset(Dataset):
    """Dataset loader for CodeXGLUE Devign code vulnerability dataset."""

    def __init__(self, file_path: str, tokenizer=None, max_length: int = 256):
        self.file_path = Path(file_path)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.samples: List[Dict[str, Any]] = []

        self._load_data()

    def _load_data(self):
        """Loads JSONL records: {'func': '...', 'target': 0 or 1}."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Dataset split not found: {self.file_path}")

        with open(self.file_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        func_code = record.get("func") or record.get("code") or ""
                        target = int(record.get("target", 0))
                        if func_code:
                            self.samples.append({
                                "func": func_code,
                                "target": target
                            })
                    except Exception:
                        continue

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        func_text = sample["func"]
        label = sample["target"]

        if self.tokenizer and HAS_TORCH:
            encoding = self.tokenizer(
                func_text,
                truncation=True,
                max_length=self.max_length,
                padding="max_length",
                return_tensors="pt"
            )
            return {
                "input_ids": encoding["input_ids"].squeeze(0),
                "attention_mask": encoding["attention_mask"].squeeze(0),
                "labels": torch.tensor(label, dtype=torch.long)
            }
        else:
            return {
                "func": func_text,
                "label": label
            }
