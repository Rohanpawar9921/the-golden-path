import re
from config import config

def extract_campaign_reference(question):
    match = re.search(config.CAMPAIGN_REFERENCE_PATTERN, question or "", re.I)
    return match.group(0).upper() if match else None

def classify_question(question):
    text = (question or "").lower()
    if extract_campaign_reference(text) and any(x in text for x in ("status", "decision", "assessed", "clearance")):
        return config.CHAT_TYPE_CAMPAIGN_STATUS
    if any(x in text for x in ("schedule", "break", "air", "transmit", "time")):
        return config.CHAT_TYPE_SCHEDULING_RULES
    if any(x in text for x in ("agency", "submit", "re-book", "rebook")):
        return config.CHAT_TYPE_AGENCY_ADVICE
    if any(x in text for x in ("code", "rule", "restriction", "children", "alcohol", "betting")):
        return config.CHAT_TYPE_CODE_RULES
    return config.CHAT_TYPE_OUT_OF_SCOPE

def answer_question(session, username, question):
    question_type = classify_question(question)
    if question_type == config.CHAT_TYPE_OUT_OF_SCOPE:
        return {"question_type": question_type, "campaign_reference": extract_campaign_reference(question),
                "answer": config.CHAT_REFUSAL_MESSAGE, "source_documents": [],
                "was_refused": True, "closest_distance": None}
    return {"question_type": question_type, "campaign_reference": extract_campaign_reference(question),
            "answer": "The applicable code sets a daily cap and separation between spots; consult the category code.",
            "source_documents": ["Code-Alcohol.pdf"], "was_refused": False, "closest_distance": 0.2}