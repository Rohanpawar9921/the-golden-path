"""Grounded chat classification and answer generation over Harbourlight documents."""

from __future__ import annotations

import re

from agentic.agents import LanguageModelUnavailable, call_language_model, parse_labelled_response
from config import config
from knowledge.vector_index import read_document_chunks, search_documents


def extract_campaign_reference(question_text: str | None) -> str | None:
    match = re.search(config.CAMPAIGN_REFERENCE_PATTERN, question_text or "", re.I)
    return match.group(0).upper() if match else None


def classify_question(question_text: str | None) -> str:
    """Conservative local classifier used only when the model SDK is unavailable."""
    text = (question_text or "").lower()
    reference = extract_campaign_reference(text)
    if reference and any(term in text for term in
                         ("status", "decision", "assessed", "clearance", "progress", "where")):
        return config.CHAT_TYPE_CAMPAIGN_STATUS
    categories = [name.lower() for name in config.CATEGORY_CODE_DOCUMENTS]
    category_terms = categories + ["alcoholic", "gambling", "betting", "credit", "medicine", "health"]
    asks_about_rules = any(term in text for term in
                           ("code", "rule", "restriction", "allowed", "limit", "how many",
                            "how far", "threshold", "children", "under-18", "spots"))
    if asks_about_rules or any(term in text for term in category_terms):
        return config.CHAT_TYPE_CODE_RULES
    if any(term in text for term in ("agency", "submit", "re-book", "rebook", "re-booking")):
        return config.CHAT_TYPE_AGENCY_ADVICE
    if any(term in text for term in
           ("schedule", "break", "air", "transmit", "transmission", "airing", "time", "clock")):
        return config.CHAT_TYPE_SCHEDULING_RULES
    return config.CHAT_TYPE_OUT_OF_SCOPE


def _category_for_question(question_text: str) -> str | None:
    text = re.sub(r"[^a-z0-9]+", " ", (question_text or "").lower())
    aliases = {
        "Alcohol": ("alcohol", "alcoholic drinks"),
        "Betting and gaming": ("betting", "gaming", "gambling"),
        "Less healthy food": ("less healthy food", "hfss", "unhealthy food"),
        "Consumer credit": ("consumer credit", "credit", "loan", "apr", "buy now pay later"),
        "Medicines and health": ("medicines and health", "medicine", "medicines", "health"),
    }
    for category, terms in aliases.items():
        if any(re.search(r"\b" + re.escape(term) + r"\b", text) for term in terms):
            return category
    return None


def _unique_passages(question_passages, context_passages):
    result, seen = [], set()
    for passages in (question_passages, context_passages):
        for passage in passages:
            identity = passage.get("chunk_id") or (
                passage.get("document_name"), passage.get("chunk_text")
            )
            if identity in seen:
                continue
            seen.add(identity)
            result.append(passage)
    return result


def _build_prompt(question_text, conversation, question_passages,
                  context_passages, full_codes):
    code_sections = []
    for category, document_name in config.CATEGORY_CODE_DOCUMENTS.items():
        body = "\n".join(full_codes[category])
        code_sections.append(f"CATEGORY: {category}\nDOCUMENT: {document_name}\n{body}")

    passages = _unique_passages(question_passages, context_passages)
    passage_sections = [
        f"[{item['document_name']} | distance={item['distance']:.4f}]\n{item['chunk_text']}"
        for item in passages
    ]
    history = conversation.get("history_text") or "This is the first question in this conversation."
    search_text = conversation.get("search_text") or question_text
    return "\n\n".join([
        "You are Harbourlight Media's clearance assistant. Answer only from the supplied policy "
        "documents and passages. Do not use outside knowledge, invent a rule, or infer a campaign "
        "fact. The campaign database is not included and you know nothing about campaign records.",
        "Classify the user's question as exactly one of: " + ", ".join(config.CHAT_TYPE_OPTIONS) + ". "
        "Use CAMPAIGN STATUS only for a question about one named campaign's recorded status. "
        "Use CODE RULES for category-code questions, SCHEDULING RULES for broadcast timing or "
        "placement, AGENCY ADVICE for agency process, and OUT OF SCOPE if the evidence does not "
        "answer it. A short follow-up without a subject continues the last exchange in the "
        "conversation. Always name the category when stating a category rule, and take figures "
        "only from that category's own code.",
        "Return exactly these three labelled fields, in this order, with no extra headings:\n"
        "QUESTION TYPE: one of the five exact types above\n"
        f"CAMPAIGN REFERENCE: one reference in the form {config.CAMPAIGN_REFERENCE_FORM}, or "
        f"{config.CHAT_NO_VALUE_REPLY}\n"
        "ANSWER: a concise answer grounded in the supplied evidence; for CAMPAIGN STATUS say "
        "that the service must look up the campaign record; for OUT OF SCOPE use none.",
        "FIVE CATEGORY CODES (each code is supplied in full; do not transfer a figure or rule "
        "from one category to another):\n" + "\n\n".join(code_sections),
        "PASSAGES RETRIEVED FOR THE QUESTION AND THE CONVERSATION SEARCH TEXT (each passage once; "
        "the casebook is excluded):\n" + ("\n\n".join(passage_sections) or "No passages found."),
        "RECENT CONVERSATION (campaign status answers are replaced with a safe placeholder):\n" + history,
        "SEARCH TEXT USED FOR FOLLOW-UP CONTEXT:\n" + search_text,
        "USER QUESTION:\n" + question_text,
    ])


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for",
    "from", "go", "how", "i", "in", "is", "it", "may", "me", "must", "of", "on",
    "one", "or", "should", "the", "their", "this", "to", "we", "what", "when", "where",
    "which", "who", "with", "would",
}


def _rule_excerpt(question_text, category, full_codes):
    """Select the exact rule sentence requested from that category's own code."""
    text = "\n".join(full_codes[category])
    rules = []
    for name, pattern in config.CHILDREN_RULE_PATTERNS.items():
        match = re.search(pattern, text)
        if match:
            rules.append(("children", match.group(0)))
    for code, pattern in config.CODE_FIGURE_PATTERNS.items():
        match = re.search(pattern, text)
        if match:
            kind = {"index_threshold": "index", "daily_cap": "frequency",
                    "separation_minutes": "separation"}[code]
            rules.append((kind, match.group(0)))
    hours = re.search(config.RESTRICTED_HOURS_PATTERN, text)
    any_time = re.search(config.ANY_TIME_PATTERN, text)
    if hours:
        rules.append(("hours", hours.group(0)))
    elif any_time:
        rules.append(("hours", any_time.group(0)))
    exception = re.search(config.LIVE_SPORT_EXCEPTION_PATTERN, text)
    if exception:
        rules.append(("live sport", exception.group(0)))

    question = question_text.lower()
    if any(word in question for word in ("separate", "apart", "spacing", "interval")):
        wanted = "separation"
    elif any(word in question for word in ("how many", "daily cap", "per day", "limit", "maximum")):
        wanted = "frequency"
    elif any(word in question for word in ("children", "child", "young people", "under-18", "under 18")):
        wanted = "children" if "index" not in question and "audience" not in question else "index"
    elif any(word in question for word in ("index", "audience threshold", "audience level")):
        wanted = "index"
    elif any(word in question for word in ("live sport", "exception")):
        wanted = "live sport" if exception else "hours"
    elif any(word in question for word in ("hour", "time", "when", "air", "transmit", "restricted")):
        wanted = "hours"
    else:
        wanted = None

    chosen = next((sentence for kind, sentence in rules if kind == wanted), None)
    if not chosen and rules:
        chosen = max(rules, key=lambda item: len(
            set(re.findall(r"[a-z0-9]+", question))
            & set(re.findall(r"[a-z0-9]+", item[1].lower()))
        ))[1]
    return f"The {category} code says: {chosen}" if chosen else None


def _extractive_answer(question_text, passages, full_codes):
    """Produce a question-specific evidence excerpt when Gemini is not installed."""
    category = _category_for_question(question_text)
    if category:
        answer = _rule_excerpt(question_text, category, full_codes)
        if answer:
            return answer

    candidates = []
    if category:
        document_name = config.CATEGORY_CODE_DOCUMENTS[category]
        candidates.extend((document_name, text) for text in full_codes[category])
    candidates.extend((item["document_name"], item["chunk_text"]) for item in passages)

    query_words = {word for word in re.findall(r"[a-z0-9]+", question_text.lower())
                   if word not in _STOPWORDS}
    best = None
    for document_name, passage in candidates:
        if document_name in config.CHAT_EXCLUDED_DOCUMENTS:
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", passage):
            words = set(re.findall(r"[a-z0-9]+", sentence.lower()))
            overlap = query_words & words
            score = len(overlap) / max(1, len(query_words))
            if category and document_name == config.CATEGORY_CODE_DOCUMENTS[category]:
                score += 0.35
            if len(sentence) > 700:
                score -= 0.1
            candidate = (score, sentence.strip(), document_name)
            if best is None or candidate[0] > best[0]:
                best = candidate
    if best and best[0] >= 0.35:
        return best[1]
    return config.CHAT_REFUSAL_MESSAGE


def _parse_reply(response_text):
    fields = parse_labelled_response(
        response_text,
        labels=["QUESTION TYPE", "CAMPAIGN REFERENCE", "ANSWER"],
        context=config.AGENT_NAME_CLEARANCE_ASSISTANT,
    )
    question_type = fields["QUESTION TYPE"].strip()
    campaign_reference = fields["CAMPAIGN REFERENCE"].strip()
    answer = fields["ANSWER"].strip()
    if any("\n" in value for value in (question_type, campaign_reference)):
        raise ValueError("The clearance assistant returned a multi-line type or campaign reference.")
    if question_type not in config.CHAT_TYPE_OPTIONS:
        raise ValueError(f"The clearance assistant returned an unknown question type: {question_type!r}.")
    if campaign_reference != config.CHAT_NO_VALUE_REPLY:
        if not re.fullmatch(config.CAMPAIGN_REFERENCE_PATTERN, campaign_reference, re.I):
            raise ValueError("The clearance assistant returned an invalid campaign reference.")
        campaign_reference = campaign_reference.upper()
    else:
        campaign_reference = None
    if question_type in config.CHAT_ANSWERED_TYPES and not answer:
        raise ValueError(f"The clearance assistant returned no answer for {question_type}.")
    return question_type, campaign_reference, answer


def answer_from_documents(collection, question_text, conversation):
    """Retrieve policy evidence, generate one grounded reply, and refuse weak matches."""
    search_text = conversation.get("search_text") or question_text
    retrieved = search_documents(collection, [question_text, search_text])
    question_passages = retrieved[0] if retrieved else []
    context_passages = retrieved[1] if len(retrieved) > 1 else []
    offered_passages = _unique_passages(question_passages, context_passages)
    full_codes = {
        category: read_document_chunks(collection, document_name)
        for category, document_name in config.CATEGORY_CODE_DOCUMENTS.items()
    }
    prompt = _build_prompt(question_text, conversation, question_passages,
                           context_passages, full_codes)

    generation_mode = "gemini"
    call_record = None
    try:
        generated = call_language_model(prompt, config.AGENT_NAME_CLEARANCE_ASSISTANT)
        if isinstance(generated, dict):
            response_text = generated.get("response_text", "")
            call_record = generated.get("call_record")
        else:  # Allows small client adapters to return plain text.
            response_text = str(generated or "")
    except LanguageModelUnavailable:
        generation_mode = "retrieval fallback"
        guessed_type = classify_question(question_text)
        guessed_reference = extract_campaign_reference(question_text)
        response_text = (
            f"QUESTION TYPE: {guessed_type}\n"
            f"CAMPAIGN REFERENCE: {guessed_reference or config.CHAT_NO_VALUE_REPLY}\n"
            "ANSWER: " + (
                _extractive_answer(question_text, offered_passages, full_codes)
                if guessed_type in config.CHAT_ANSWERED_TYPES
                else ("The service will look up the campaign record."
                      if guessed_type == config.CHAT_TYPE_CAMPAIGN_STATUS
                      else "none")
            )
        )

    question_type, campaign_reference, model_answer = _parse_reply(response_text)
    nearest_distance = min((float(item["distance"]) for item in offered_passages), default=1.0)
    source_documents = list(dict.fromkeys(item["document_name"] for item in offered_passages))
    if question_type == config.CHAT_TYPE_OUT_OF_SCOPE:
        return {
            "question_type": question_type,
            "campaign_reference": campaign_reference,
            "answer": config.CHAT_REFUSAL_MESSAGE,
            "source_documents": [],
            "closest_distance": nearest_distance,
            "was_refused": True,
            "generation_mode": generation_mode,
            "call_record": call_record,
        }

    if question_type != config.CHAT_TYPE_CAMPAIGN_STATUS \
            and nearest_distance > config.CHAT_MAX_RELEVANCE_DISTANCE:
        return {
            "question_type": config.CHAT_TYPE_OUT_OF_SCOPE,
            "campaign_reference": campaign_reference,
            "answer": config.CHAT_REFUSAL_MESSAGE,
            "source_documents": [],
            "closest_distance": nearest_distance,
            "was_refused": True,
            "generation_mode": generation_mode,
            "call_record": call_record,
        }

    if question_type == config.CHAT_TYPE_CAMPAIGN_STATUS:
        # The service replaces this text with the campaign record after enforcing
        # the liaison ownership boundary. Campaign facts never enter the prompt.
        model_answer = model_answer or "The service will look up the campaign record."
        source_documents = []
    elif question_type == config.CHAT_TYPE_CODE_RULES:
        source_documents = list(dict.fromkeys(
            list(config.CATEGORY_CODE_DOCUMENTS.values()) + source_documents
        ))

    return {
        "question_type": question_type,
        "campaign_reference": campaign_reference,
        "answer": model_answer,
        "source_documents": source_documents,
        "closest_distance": nearest_distance,
        "was_refused": False,
        "generation_mode": generation_mode,
        "call_record": call_record,
    }
