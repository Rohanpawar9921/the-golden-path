"""Grounding and answer-generation checks for the clearance assistant."""

from config import config
from knowledge.vector_index import open_vector_index


def test_one_model_call_receives_each_category_code_and_question_context(monkeypatch):
    import chat.clearance_assistant as assistant

    collection = open_vector_index(config.VECTOR_STORE_DIRECTORY)
    calls = []

    def fake_model(prompt_text, agent_name):
        calls.append((prompt_text, agent_name))
        return {
            "response_text": (
                "QUESTION TYPE: CODE RULES\n"
                "CAMPAIGN REFERENCE: none\n"
                "ANSWER: The Alcohol code permits the number stated in its daily limit."
            ),
            "call_record": {"agent_name": agent_name, "model_name": "test-model"},
        }

    monkeypatch.setattr(assistant, "call_language_model", fake_model)
    question = "How many spots may an Alcohol campaign book per channel each day?"
    result = assistant.answer_from_documents(
        collection,
        question,
        {"history_text": "This is the first question in this conversation.",
         "search_text": question},
    )

    assert len(calls) == 1
    assert calls[0][1] == config.AGENT_NAME_CLEARANCE_ASSISTANT
    assert question in calls[0][0]
    assert all(document in calls[0][0] for document in config.CATEGORY_CODE_DOCUMENTS.values())
    assert result["question_type"] == config.CHAT_TYPE_CODE_RULES
    assert result["source_documents"][:5] == list(config.CATEGORY_CODE_DOCUMENTS.values())
    assert result["was_refused"] is False


def test_offline_retrieval_answers_different_questions_from_their_own_codes(monkeypatch):
    import chat.clearance_assistant as assistant

    collection = open_vector_index(config.VECTOR_STORE_DIRECTORY)

    def unavailable(*_args, **_kwargs):
        raise assistant.LanguageModelUnavailable("offline test")

    monkeypatch.setattr(assistant, "call_language_model", unavailable)
    conversation = {"history_text": "This is the first question in this conversation."}
    alcohol_question = "How many spots can one Alcohol campaign run per channel in one day?"
    betting_question = "How far apart must Betting and gaming campaign spots be?"
    alcohol = assistant.answer_from_documents(
        collection, alcohol_question, {**conversation, "search_text": alcohol_question}
    )
    betting = assistant.answer_from_documents(
        collection, betting_question, {**conversation, "search_text": betting_question}
    )

    assert alcohol["generation_mode"] == "retrieval fallback"
    assert "Alcohol code" in alcohol["answer"]
    assert "daily" in alcohol["answer"] or "spots" in alcohol["answer"]
    assert "Betting and gaming code" in betting["answer"]
    assert "minutes apart" in betting["answer"]
    assert alcohol["answer"] != betting["answer"]

    unrelated_question = "What is the capital of France?"
    unrelated = assistant.answer_from_documents(
        collection, unrelated_question,
        {**conversation, "search_text": unrelated_question},
    )
    assert unrelated["question_type"] == config.CHAT_TYPE_OUT_OF_SCOPE
    assert unrelated["was_refused"] is True
    assert unrelated["source_documents"] == []


def test_gemini_rest_transport_makes_one_authenticated_generation_call(monkeypatch):
    import agentic.agents as agents
    import requests

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{"text": "A generated answer."}]},
            }]}

    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse()

    monkeypatch.setenv(config.GEMINI_API_KEY_VARIABLE, "test-key")
    monkeypatch.setenv(config.GEMINI_MODEL_VARIABLE, "test-model")
    monkeypatch.delenv("BREAKCHECK_CHAT_OFFLINE", raising=False)
    monkeypatch.setattr(agents, "genai_types", None)
    monkeypatch.setattr(requests, "post", fake_post)

    reply = agents.call_language_model("A grounded test prompt", "clearance_assistant")

    assert len(calls) == 1
    assert calls[0][0].endswith("/models/test-model:generateContent")
    assert calls[0][1]["headers"]["x-goog-api-key"] == "test-key"
    assert "test-key" not in calls[0][0]
    assert reply["response_text"] == "A generated answer."
    assert reply["call_record"]["prompt_characters"] == len("A grounded test prompt")
