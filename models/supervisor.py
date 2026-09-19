from enum import Enum

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    FINANCIAL = "financial"
    RESEARCH = "research"
    NEWS = "news"


class SupervisorPlan(BaseModel):
    company_name: str = Field(
        description=(
            "Extract only the company name explicitly mentioned by the user. "
            "Do not use outside knowledge. "
            "Do not infer, correct, rename, expand, or substitute the company name. "
            "Preserve the company name as the user provided it."
        )
    )
    agents: list[AgentType] = Field(
        description=(
            "The specialized agents required to answer the user's question. "
            "Choose one or more from financial, research, and news."
        )
    )