"""
agent/llm_engine.py
AI-Powered Fix Synthesizer and Error Remediation Engine.
Supports:
1. Google Gemini API (gemini-2.5-flash / gemini-1.5-flash) if GEMINI_API_KEY is present
2. Local Open-Source Ollama models (Qwen2.5-Coder / DeepSeek-Coder / CodeLlama)
3. Graceful fallback to deterministic AST rule patch synthesis
"""

import os
import re
import json
import logging
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger("CodeAuditor.LLMEngine")

# Default models
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-3.5-flash", "gemini-flash-latest"]
OLLAMA_MODELS = ["qwen2.5-coder:1.5b", "qwen2.5-coder", "deepseek-coder:1.3b", "codellama"]


def _clean_markdown_code_fences(text: str) -> str:
    """Strips markdown code blocks (```python ... ```) if returned by the LLM."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop the opening ```python
        lines = lines[1:]
        # Drop the closing ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def generate_ai_remediation(
    category: str,
    cwe_id: str,
    vulnerable_code: str,
    file_path: str = "snippet.py",
    error_details: Optional[str] = None,
    language: Optional[str] = None
) -> Optional[str]:
    """
    Synthesizes custom, context-aware remediation code using an LLM.
    Returns None if no LLM service is reachable, allowing fallback to AST rewriter.
    """
    # 1. Infer target language
    target_lang = language
    if not target_lang:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in (".js", ".jsx", ".mjs", ".cjs", ".html", ".htm"):
            target_lang = "javascript"
        elif ext in (".ts", ".tsx"):
            target_lang = "typescript"
        elif ext in (".c", ".h"):
            target_lang = "c"
        elif ext in (".cpp", ".hpp", ".cc"):
            target_lang = "cpp"
        elif ext in (".java",):
            target_lang = "java"
        else:
            target_lang = "python"

    comment_char = "//" if target_lang in ("javascript", "typescript", "java", "c", "cpp") else "#"

    # 2. Build prompt with strict completeness instructions
    prompt = (
        f"You are a principal security engineer and senior software architect.\n"
        f"A vulnerability has been detected in the following {target_lang.capitalize()} code snippet:\n"
        f"- File: {file_path}\n"
        f"- Vulnerability Category: {category} ({cwe_id})\n"
    )
    if error_details:
        prompt += f"- Error Details: {error_details}\n"

    prompt += (
        f"\nVulnerable Code:\n"
        f"{vulnerable_code}\n\n"
        f"Task:\n"
        f"Write the EXACT drop-in replacement for the code above that remediates the {category} vulnerability.\n"
        f"CRITICAL RULES:\n"
        f"1. You MUST reproduce the COMPLETE code block from start to finish. Do NOT truncate, do NOT omit lines, and do NOT use placeholders like '// ... remaining code'.\n"
        f"2. Do NOT invent or declare new helper functions above or below the code block (assume standard libraries or sanitizers are available).\n"
        f"3. Preserve all original variable names, control flow, and functionality while applying the secure pattern.\n"
        f"4. Output ONLY raw executable code. No markdown code blocks (no ```). No conversational explanations."
    )

    # 2. Try Google Gemini API
    keys_to_try = []
    # Project .env key first
    if os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GEMINI_API_KEY="):
                        k = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                        if k and k not in keys_to_try:
                            keys_to_try.append(k)
                        break
        except Exception:
            pass

    env_os_key = os.getenv("GEMINI_API_KEY")
    if env_os_key and env_os_key not in keys_to_try:
        keys_to_try.append(env_os_key)

    for gemini_key in keys_to_try:
        for model in GEMINI_MODELS:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 2048
                    }
                }
                resp = requests.post(url, json=payload, timeout=12)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            code_text = _clean_markdown_code_fences(parts[0]["text"])
                            return f"{comment_char} Grounded Fix ({cwe_id}) [AI-Remediated]:\n" + code_text
            except Exception as e:
                logger.debug(f"Gemini generation failed on {model}: {e}")

    # 3. Try Local Open-Source Ollama (Qwen2.5-Coder / DeepSeek-Coder)
    try:
        ollama_url = "http://localhost:11434/api/generate"
        for o_model in OLLAMA_MODELS:
            payload = {
                "model": o_model,
                "prompt": prompt,
                "stream": False
            }
            resp = requests.post(ollama_url, json=payload, timeout=4)
            if resp.status_code == 200:
                text = resp.json().get("response", "").strip()
                if text:
                    code_text = _clean_markdown_code_fences(text)
                    return f"# Grounded Fix ({cwe_id}) [Local AI Patch]:\n" + code_text
    except Exception as e:
        logger.debug(f"Ollama local inference unavailable: {e}")

    # 4. Fallback to None (caller will use deterministic AST rewriter)
    return None
