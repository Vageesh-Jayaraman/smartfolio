from pydantic import BaseModel, Field

from models.financial_period import FinancialPeriod


class ResearchTask(BaseModel):
    topic: str = Field(
        description="The research area being investigated."
    )

    search_query: str = Field(
        description=(
            "A specific, context-rich semantic search query. "
            "Include the company, financial period, metric, "
            "and information being investigated."
        )
    )

    periods: list[FinancialPeriod] = Field(
        description="Financial periods relevant to this research task."
    )
