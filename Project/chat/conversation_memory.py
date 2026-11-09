from sqlalchemy import select
from persistence.models import ChatTurn
from config import config
def recall_conversation(session, username, question):
    rows = list(session.scalars(select(ChatTurn).where(ChatTurn.username == username)
                                .order_by(ChatTurn.id.desc()).limit(3)))
    rows.reverse()
    history = "\n".join((r.question_text if not r.was_refused else r.question_text) + "\n" +
                        (config.CHAT_STATUS_ANSWER_IN_HISTORY if r.question_type == config.CHAT_TYPE_CAMPAIGN_STATUS
                         else (r.answer_text or "")) for r in rows)
    return {"history_text": history, "search_text": (history + "\n" + question).strip()}