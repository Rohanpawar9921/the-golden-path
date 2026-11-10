"""Recall only the signed-in person's recent, safe chat context."""

from sqlalchemy import select

from config import config
from persistence.models import ChatTurn


def recall_conversation(session, username, question_text):
    rows = list(session.scalars(
        select(ChatTurn)
        .where(ChatTurn.username == username)
        .order_by(ChatTurn.id.desc())
        .limit(config.CHAT_HISTORY_TURN_LIMIT)
    ))
    rows.reverse()
    exchanges = []
    for row in rows:
        if row.question_type == config.CHAT_TYPE_CAMPAIGN_STATUS:
            safe_answer = config.CHAT_STATUS_ANSWER_IN_HISTORY
        else:
            safe_answer = row.answer_text or ""
        exchanges.append(f"Question: {row.question_text}\nAnswer: {safe_answer}")

    history_text = "\n\n".join(exchanges) or "This is the first question in this conversation."
    previous_question = rows[-1].question_text if rows else ""
    search_text = "\n".join(part for part in (previous_question, question_text) if part)
    return {"history_text": history_text, "search_text": search_text}
