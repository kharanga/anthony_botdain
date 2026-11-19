from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from travel_companion.cards import AnswerCard, Evidence
from travel_companion.chat_message import ChatMessage
from travel_companion.model_client import ModelClient, ModelUnavailable

ASK_SYSTEM_PROMPT = "You are a travel companion. Answer the traveller's question briefly in plain English."


class AskRequest(BaseModel):
    question: str


def answer_card_from_model(question: str, model_client: ModelClient) -> AnswerCard:
    answer = model_client.complete(
        [ChatMessage("system", ASK_SYSTEM_PROMPT), ChatMessage("user", question)]
    )
    return AnswerCard(
        kind="answer",
        title=question,
        body=answer,
        evidence=[Evidence(source=model_client.endpoint_url, text=f"model answer to: {question}")],
    )


def model_unavailable_card(model_client: ModelClient, reason: str) -> AnswerCard:
    return AnswerCard(
        kind="model_unavailable",
        title="Model unavailable",
        body="The model endpoint did not answer. Check that the model server is running.",
        evidence=[Evidence(source=model_client.endpoint_url, text=reason)],
    )


ask_router = APIRouter()


@ask_router.post("/api/ask", response_model=AnswerCard)
def post_ask(ask_request: AskRequest, request: Request):
    model_client = request.app.state.model_client
    try:
        return answer_card_from_model(ask_request.question, model_client)
    except ModelUnavailable as error:
        unavailable_card = model_unavailable_card(model_client, str(error))
        return JSONResponse(status_code=503, content=unavailable_card.model_dump())
