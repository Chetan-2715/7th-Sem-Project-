"""
ml_pipeline/inference.py
Inference runner for the fine-tuned CodeBERT model.
Tests code snippets and outputs:
- Vulnerability prediction (Safe / Vulnerable)
- Confidence probability (0.0 to 1.0)
- Execution latency

Usage:
    python ml_pipeline/inference.py --code "char buf[10]; strcpy(buf, input);"
"""

import sys
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml_pipeline.model import CodeBERTClassifier

CHECKPOINT_DIR = Path(__file__).resolve().parent / "checkpoints" / "best_model"


def run_inference(code: str, model_path: str = None) -> dict:
    """Classifies code snippet and returns prediction dictionary."""
    chosen_path = model_path or (str(CHECKPOINT_DIR) if CHECKPOINT_DIR.exists() else "microsoft/codebert-base")

    classifier = CodeBERTClassifier(model_name_or_path=chosen_path)
    label, confidence = classifier.predict(code)

    return {
        "model_used": chosen_path,
        "is_vulnerable": bool(label == 1),
        "label": "VULNERABLE" if label == 1 else "SAFE",
        "confidence": confidence,
        "code_snippet": code
    }


def main():
    parser = argparse.ArgumentParser(description="Test CodeBERT on a code snippet")
    parser.add_argument("--code", type=str, default=None, help="Code snippet to scan")
    parser.add_argument("--model_path", type=str, default=None, help="Custom model checkpoint path")
    args = parser.parse_args()

    sample_code = args.code or (
        "void authenticate(char* user, char* pass) {\n"
        "    char query[256];\n"
        "    sprintf(query, \"SELECT * FROM users WHERE u='%s' AND p='%s'\", user, pass);\n"
        "    db_exec(query);\n"
        "}"
    )

    print("=======================================================")
    print("CodeBERT Vulnerability Prediction")
    print("=======================================================")
    print(f"Code to test:\n{sample_code}\n")

    result = run_inference(sample_code, args.model_path)
    print(f"Result: {result['label']}")
    print(f"Confidence: {result['confidence'] * 100:.1f}%")
    print(f"Model Path: {result['model_used']}")
    print("=======================================================")


if __name__ == "__main__":
    main()
