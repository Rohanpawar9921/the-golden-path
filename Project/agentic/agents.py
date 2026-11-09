import os, json, re
try:
    from config import config
except ImportError:
    from Project.config import config
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