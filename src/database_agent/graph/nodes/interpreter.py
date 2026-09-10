# src/database_agent/graph/nodes/interpreter.py

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from database_agent.core.config import get_settings
from database_agent.graph.prompts import INTERPRETER_PROMPT
from database_agent.graph.state import AgentState


class InterpretationResponse(BaseModel):
    answer: str = Field(description="A clear, direct natural language answer to the user's question, based only on the given result rows")


def _get_llm() -> ChatOllama:
    settings = get_settings()
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0,
    )


async def interpreter_node(state: AgentState) -> dict:
    llm = _get_llm().with_structured_output(InterpretationResponse)
    chain = INTERPRETER_PROMPT | llm

    response: InterpretationResponse = await chain.ainvoke(
        {
            "question": state["question"],
            "result_rows": state["result_rows"],
        }
    )
    return {"answer": response.answer}