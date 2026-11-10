import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_PROJECT_ROOT / ".env")

try:
    from config import config
except ImportError:
    from Project.config import config

try:
    from google.genai import types as genai_types

    generation_settings = genai_types.GenerateContentConfig(
        max_output_tokens=config.GEMINI_MAX_OUTPUT_TOKENS,
        temperature=config.GEMINI_TEMPERATURE,
    )
except ImportError:  # Keep document retrieval usable when the optional SDK is absent.
    genai_types = None
    generation_settings = None


class LanguageModelUnavailable(RuntimeError):
    """The configured language model client cannot be used in this environment."""


def call_language_model(prompt_text, agent_name):
    """Make one configured Gemini call and return its text and timing metadata."""
    load_dotenv(_PROJECT_ROOT / ".env")
    api_key = os.getenv(config.GEMINI_API_KEY_VARIABLE)
    model_name = os.getenv(config.GEMINI_MODEL_VARIABLE)
    if os.getenv("BREAKCHECK_CHAT_OFFLINE", "").strip().lower() in {"1", "true", "yes"}:
        raise LanguageModelUnavailable("Gemini generation was disabled for this test run.")
    if not api_key or not model_name:
        raise LanguageModelUnavailable(
            "Set both " + config.GEMINI_API_KEY_VARIABLE + " and "
            + config.GEMINI_MODEL_VARIABLE + " in the environment or Project/.env."
        )
    started = time.perf_counter()
    if genai_types is not None:
        from google import genai

        try:
            response = genai.Client(api_key=api_key).models.generate_content(
                model=model_name,
                contents=prompt_text,
                config=generation_settings,
            )
        except Exception as error:
            raise LanguageModelUnavailable(
                f"The configured Gemini service could not be reached for {agent_name}."
            ) from error
        response_text = (getattr(response, "text", None) or "").strip()
        candidates = getattr(response, "candidates", None) or []
        finish_reason = getattr(candidates[0], "finish_reason", None) if candidates else "STOP"
        finish_name = getattr(finish_reason, "name", str(finish_reason)).upper().split(".")[-1]
    else:
        # Keep the same live model path available in light installations where
        # google-genai has not yet been installed. The key is sent as a header,
        # never placed in the request URL or logged.
        import requests

        endpoint = ("https://generativelanguage.googleapis.com/v1beta/models/"
                    + model_name + ":generateContent")
        try:
            response = requests.post(
                endpoint,
                headers={"x-goog-api-key": api_key},
                json={
                    "contents": [{"role": "user", "parts": [{"text": prompt_text}]}],
                    "generationConfig": {
                        "maxOutputTokens": config.GEMINI_MAX_OUTPUT_TOKENS,
                        "temperature": config.GEMINI_TEMPERATURE,
                    },
                },
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            raise LanguageModelUnavailable(
                f"The configured Gemini service could not be reached for {agent_name}."
            ) from error
        payload = response.json()
        candidates = payload.get("candidates") or []
        finish_name = str(candidates[0].get("finishReason", "")) if candidates else ""
        parts = (candidates[0].get("content") or {}).get("parts") or [] if candidates else []
        response_text = "".join(str(part.get("text", "")) for part in parts).strip()

    elapsed = max(0, round((time.perf_counter() - started) * 1000))
    if finish_name not in {"STOP", "FINISH_REASON_STOP"}:
        raise ValueError(
            f"{agent_name} received an incomplete reply from {model_name} "
            f"(finish reason: {finish_name or 'unknown'})."
        )
    if not response_text:
        raise ValueError(f"{agent_name} received an empty reply from {model_name}.")

    return {
        "response_text": response_text,
        "call_record": {
            "agent_name": agent_name,
            "model_name": model_name,
            "prompt_characters": len(prompt_text),
            "response_characters": len(response_text),
            "latency_milliseconds": elapsed,
        },
    }


def _fallback(agent_name,prompt):
    return json.dumps({"agent":agent_name,"summary":"Deterministic assessment completed","recommendation":"REVIEW","source":"fallback"})
def call_model(agent_name, prompt, repository=None, run_id=None):
    key=os.getenv(config.GEMINI_API_KEY_VARIABLE); fallback=True
    text=_fallback(agent_name,prompt)
    if key:
        try:
            from google import genai
            response=genai.Client(api_key=key).models.generate_content(model=os.getenv(config.GEMINI_MODEL_VARIABLE,"gemini-2.0-flash"),contents=prompt)
            text=response.text; fallback=False
        except Exception: pass
    if repository: repository.record_llm_call(run_id=run_id,agent_name=agent_name,prompt=prompt,response=text,model=os.getenv(config.GEMINI_MODEL_VARIABLE,"fallback"),used_fallback=fallback)
    return text

def parse_labelled_response(response, labels=None, context=None):
    """Parse a model's labelled sections without treating markdown decoration as data.

    Agents frequently return headings such as ``**Decision:**`` or bullet-prefixed
    labels.  Only the decoration surrounding a label is removed; punctuation and
    formatting in the section body are retained verbatim.
    """
    if response is None:
        return {}
    text = str(response).replace("\r\n", "\n").replace("\r", "\n")
    wanted = list(labels or [])
    result = {}
    if not wanted:
        # A conservative default also makes this useful for arbitrary agent output.
        wanted = ["decision", "summary", "recommendation", "reason", "risks",
                  "restrictions", "assessment", "sources"]
    escaped = "|".join(re.escape(x) for x in sorted(wanted, key=len, reverse=True))
    pattern = re.compile(
        r"(?im)^[\s>*#`_~•\-–—]*(?P<label>" + escaped +
        r")\s*(?:\[[^\]]+\])?\s*:\s*")
    matches = list(pattern.finditer(text))
    if not matches:
        return {}
    for index, match in enumerate(matches):
        raw_key = match.group("label").strip()
        key = next((x for x in wanted if x.lower() == raw_key.lower()), raw_key)
        value = text[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(text)]
        # Decoration belongs to the heading, not to the captured section.
        value = value.strip().strip("".join(getattr(config, "RESPONSE_DECORATION_CHARACTERS", ""))).strip()
        if not value:
            raise ValueError(f"{context or 'response'} is missing a value for {raw_key}")
        if key in result:
            result[key] += "\n" + value
        else:
            result[key] = value
    missing = [label for label in (labels or []) if label not in result or not result[label].strip()]
    if missing:
        raise ValueError(f"{context or 'response'} is missing labelled fields: {', '.join(missing)}")
    return result
