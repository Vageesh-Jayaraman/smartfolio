import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openrouter import ChatOpenRouter

from models.news_plan import NewsPlan
from prompts.news_planner import NEWS_PLANNER_PROMPT
from tools.news_search import search_news

load_dotenv()

planner_model = ChatOpenRouter(
    model="google/gemini-2.5-flash-lite",
    temperature=0,
    api_key=os.getenv("OPENROUTER_API_KEY"),
).with_structured_output(NewsPlan)


def create_news_plan(user_question: str, company_name: str) -> NewsPlan:

    return planner_model.invoke(
        [
            SystemMessage(content=NEWS_PLANNER_PROMPT),
            HumanMessage(
                content=(
                    f"Company: {company_name}\n"
                    f"User question: {user_question}"
                )
            ),
        ]
    )


def retrieve_news(news_plan: NewsPlan, max_results: int = 5):
    evidence = []

    for i, task in enumerate(news_plan.tasks):
        print(
            f"\nSearching task {i}/{len(news_plan.tasks)}: "
            f"{task.topic}"
        )

        results = search_news(
            query=task.search_query,
            max_results=max_results,
        )

        for result in results:
            evidence.append(
                {
                    "topic": task.topic,
                    "search_query": task.search_query,
                    "result": result,
                }
            )

        print(f"Retrieved {len(results)} articles")

    return evidence

def format_news_evidence(evidence):
    formatted = []

    for i, item in enumerate(evidence):
        result = item["result"]

        formatted.append(
            f"""
            [N{i}]
            Topic: {item["topic"]}
            Search query: {item["search_query"]}
            Title: {result.get("title")}
            URL: {result.get("url")}
            Published: {result.get("published_date")}
            Score: {result.get("score")}
            
            Content:
            {result.get("content", "")}
            """
        )

    return "\n".join(formatted)


def research_news(
        user_question: str,
        company_name: str,
        symbol: str,
):
    print("\nCreating news plan...")

    news_plan = create_news_plan(
        user_question=user_question,
        company_name=company_name,
    )

    print("\nNews plan:")

    for i, task in enumerate(news_plan.tasks, start=1):
        print(
            f"{i}. {task.topic}"
            f" -> {task.search_query}"
        )

    print(f"\nCompany: {company_name}")
    print(f"Symbol: {symbol}")

    evidence = retrieve_news(
        news_plan=news_plan,
        max_results=5,
    )
    print(f"\nTotal articles retrieved: {len(evidence)}")
    return evidence