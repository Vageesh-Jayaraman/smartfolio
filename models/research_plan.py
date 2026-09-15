from pydantic import BaseModel, Field

from models.research_task import ResearchTask


class ResearchPlan(BaseModel):
    company_name: str | None = Field(
        description=(
            "The single company name or stock symbol mentioned "
            "by the user. Return null if no company is mentioned."
        )
    )

    tasks: list[ResearchTask] = Field(
        description=(
            "The complete set of research tasks required to "
            "thoroughly answer the user's question."
        )
    )
