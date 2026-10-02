"""
ml_pipeline/model.py
CodeBERT Vulnerability Classifier architecture.
Wraps microsoft/codebert-base (125M parameters) with a binary classification head.
"""

from typing import Optional, Tuple

try:
    import torch
    import torch.nn as nn
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


class CodeBERTClassifier:
    """Pre-trained and Fine-tuned CodeBERT model for code defect classification."""

    def __init__(self, model_name_or_path: str = "microsoft/codebert-base", num_labels: int = 2):
        self.model_name_or_path = model_name_or_path
        self.num_labels = num_labels
        self.model = None
        self.tokenizer = None

        if HAS_TRANSFORMERS:
            self._load()

    def _load(self):
        """Loads tokenizer and sequence classification head."""
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name_or_path,
            num_labels=self.num_labels,
            use_safetensors=True
        )

    def to(self, device):
        """Moves model to target hardware device (e.g. cuda for RTX 3050)."""
        if self.model:
            self.model.to(device)
        return self

    def predict(self, code_snippet: str, device: str = "cpu") -> Tuple[int, float]:
        """
        Runs inference on a single code snippet.
        Returns: (predicted_class [0=safe, 1=vulnerable], confidence_score)
        """
        if not HAS_TRANSFORMERS or not self.model or not self.tokenizer:
            # Fallback heuristic if PyTorch/transformers are not available
            return (0, 0.5)

        self.model.eval()
        inputs = self.tokenizer(
            code_snippet,
            truncation=True,
            max_length=256,
            padding=True,
            return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).squeeze(0)
            pred = torch.argmax(probs).item()
            conf = probs[pred].item()

        return pred, round(conf, 4)
