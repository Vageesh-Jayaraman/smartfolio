import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openrouter import ChatOpenRouter
from models.research_plan import ResearchPlan
from prompts.research_planner import RESEARCH_PLANNER_PROMPT
from rag.embeddings import embed_query
from rag.vectorstore import search_documents

load_dotenv()

planner_model = ChatOpenRouter(
    model="google/gemini-2.5-flash",
    temperature=0,
    api_key=os.getenv("OPENROUTER_API_KEY"),
).with_structured_output(ResearchPlan)

def create_research_plan(user_question: str, company_name: str) -> ResearchPlan:
    return planner_model.invoke(
        [
            SystemMessage(content=RESEARCH_PLANNER_PROMPT),
            HumanMessage(
                content=(
                    f"Company: {company_name}\n"
                    f"User question: {user_question}"
                )
            )
        ]
    )

def retrieve_research_evidence(
        research_plan: ResearchPlan,
        symbol: str,
        limit: int = 3,
):

    evidence = []
    for i, task in enumerate(research_plan.tasks):
        print(
            f"\nSearching task "
            f"{i}/{len(research_plan.tasks)}: "
            f"{task.topic}"
        )

        query_vector = embed_query(task.search_query)
        results = search_documents(
            query_vector=query_vector,
            company=symbol,
            periods=[period.value for period in task.periods],
            limit=limit,
        )

        for result in results:
            evidence.append(
                {
                    "topic": task.topic,
                    "search_query": task.search_query,
                    "result": result,
                }
            )

        print(f"Retrieved {len(results)} documents")
    return evidence


def format_evidence(evidence):

    formatted = []

    for i, item in enumerate(evidence):

        result = item["result"]
        payload = result.payload
        metadata = payload["metadata"]

        formatted.append(
            f"""
                [E{i}]
                Topic: {item["topic"]}
                Search query: {item["search_query"]}
                Company: {metadata.get("company")}
                Period: {metadata.get("period")}
                Document type: {metadata.get("document_type")}
                Page: {metadata.get("page_no")}
                Source: {metadata.get("source")}
                
                Evidence:
                {payload["text"]}
            """
        )

    return "\n".join(formatted)


def research(
        user_question: str,
        company_name: str,
        symbol: str,
):

    print("\nCreating research plan...")

    research_plan = create_research_plan(
        user_question=user_question,
        company_name=company_name,
    )

    print("\nResearch plan:")

    for i, task in enumerate(research_plan.tasks):
        print(
            f"{i}. {task.topic}"
            f" -> {task.search_query}"
        )

    print(f"\nCompany: {company_name}")
    print(f"Symbol: {symbol}")

    evidence = retrieve_research_evidence(
        research_plan=research_plan,
        symbol=symbol,
        limit=3,
    )

    print(
        f"\nTotal evidence retrieved: "
        f"{len(evidence)}"
    )

    return evidence