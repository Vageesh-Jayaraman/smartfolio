import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openrouter import ChatOpenRouter

from models.news_plan import NewsPlan
from prompts.news_analyst import NEWS_ANALYST_PROMPT
from prompts.news_planner import NEWS_PLANNER_PROMPT
from tools.company_resolver import resolve_company
from tools.news_search import search_news

load_dotenv()

planner_model = ChatOpenRouter(
    model="google/gemini-2.5-flash-lite",
    temperature=0,
    api_key=os.getenv("OPENROUTER_API_KEY"),
).with_structured_output(NewsPlan)

analyst_model = ChatOpenRouter(
    model="z-ai/glm-5.2",
    temperature=0,
    api_key=os.getenv("OPENROUTER_API_KEY"),
    openrouter_provider={"order": ["Baidu Qianfan"]},
)


def create_news_plan(user_question: str) -> NewsPlan:
    return planner_model.invoke(
        [
            SystemMessage(content=NEWS_PLANNER_PROMPT),
            HumanMessage(content=user_question),
        ]
    )


def resolve_news_plan(news_plan: NewsPlan):
    if not news_plan.company_name:
        return news_plan, None

    result = resolve_company.invoke(
        {"company_name": news_plan.company_name}
    )

    if result["status"] != "success":
        raise ValueError(
            f"Could not resolve company: {news_plan.company_name}"
        )

    company = result["matches"][0]["symbol"]
    return news_plan, company


def retrieve_news(
        news_plan: NewsPlan,
        max_results: int = 5,
):
    evidence = []

    for i, task in enumerate(news_plan.tasks, start=1):
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


def synthesize_news(
        user_question: str,
        news_plan: NewsPlan,
        evidence,
):
    evidence_text = format_news_evidence(evidence)

    response = analyst_model.invoke(
        [
            SystemMessage(content=NEWS_ANALYST_PROMPT),
            HumanMessage(
                content=(
                    f"USER QUESTION:\n{user_question}\n\n"
                    f"NEWS PLAN:\n{news_plan}\n\n"
                    f"NEWS EVIDENCE:\n{evidence_text}"
                )
            ),
        ]
    )

    return response.content


def research_news(user_question: str):
    print("\nAnalyzing query...")

    news_plan = create_news_plan(user_question)

    print("\nNews plan:")
    for i, task in enumerate(news_plan.tasks, start=1):
        print(f"{i}. {task.topic} -> {task.search_query}")

    news_plan, company = resolve_news_plan(news_plan)

    if company:
        print(f"\nResolved company: {company}")

    evidence = retrieve_news(
        news_plan=news_plan,
        max_results=5,
    )

    print(f"\nTotal articles retrieved: {len(evidence)}")
    print("\nSending evidence to analyst model...")

    return synthesize_news(
        user_question=user_question,
        news_plan=news_plan,
        evidence=evidence,
    )