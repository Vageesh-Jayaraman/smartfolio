from pydantic import BaseModel, Field


class NewsTask(BaseModel):
    topic: str = Field(
        description="The news topic that needs to be investigated."
    )
    search_query: str = Field(
        description="A focused web search query for finding recent news."
    )


class NewsPlan(BaseModel):
    company_name: str | None = Field(
        description="The company mentioned by the user, or null if none."
    )
    tasks: list[NewsTask] = Field(
        description="Focused news research tasks."
    )