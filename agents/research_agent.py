import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openrouter import ChatOpenRouter
from models.research_plan import ResearchPlan
from prompts.research_analyst import RESEARCH_ANALYST_PROMPT
from prompts.research_planner import RESEARCH_PLANNER_PROMPT
from rag.embeddings import embed_query
from rag.vectorstore import search_documents
from tools.company_resolver import resolve_company

load_dotenv()

planner_model = ChatOpenRouter(
    model="google/gemini-2.5-flash",
    temperature=0,
    api_key=os.getenv("OPENROUTER_API_KEY"),
).with_structured_output(ResearchPlan)

kimi_model = ChatOpenRouter(
    model="moonshotai/kimi-k2.5",
    temperature=0,
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def create_research_plan(user_question: str) -> ResearchPlan:
    return planner_model.invoke(
        [
            SystemMessage(content=RESEARCH_PLANNER_PROMPT),
            HumanMessage(content=user_question)
        ]
    )


def resolve_research_plan(research_plan: ResearchPlan):
    if not research_plan.company_name:
        return research_plan, None

    result = resolve_company.invoke(
        {
            "company_name": research_plan.company_name,
        }
    )

    if result["status"] != "success":
        raise ValueError(
            f"Could not resolve company: "
            f"{research_plan.company_name}"
        )

    company = result["matches"][0]["symbol"]
    return research_plan, company


def retrieve_research_evidence(
        research_plan: ResearchPlan,
        company: str,
        limit: int = 3,
):

    evidence = []

    for i, task in enumerate(research_plan.tasks):

        print(
            f"\nSearching task "
            f"{i}/{len(research_plan.tasks)}: "
            f"{task.topic}"
        )

        query_vector = embed_query(
            task.search_query
        )

        results = search_documents(
            query_vector=query_vector,
            company=company,
            periods=[
                period.value
                for period in task.periods
            ],
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

        print(
            f"Retrieved {len(results)} documents"
        )

    return evidence


def format_evidence(evidence):

    formatted = []
    for i, item in enumerate(evidence,):
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


def synthesize_with_kimi(
        user_question: str,
        research_plan: ResearchPlan,
        evidence,
):

    evidence_text = format_evidence(evidence)

    response = kimi_model.invoke(
        [
            SystemMessage(content=RESEARCH_ANALYST_PROMPT),
            HumanMessage(
                content=(
                    f"USER QUESTION:\n"
                    f"{user_question}\n\n"
                    f"RESEARCH PLAN:\n"
                    f"{research_plan}\n\n"
                    f"RETRIEVED EVIDENCE:\n"
                    f"{evidence_text}"
                )
            ),
        ]
    )

    return response.content


def research(user_question: str,):

    print("\nAnalyzing query...")
    research_plan = create_research_plan(user_question)
    print("\nResearch plan:")

    for i, task in enumerate(research_plan.tasks):
        print(
            f"{i}. {task.topic}"
            f" -> {task.search_query}"
        )

    research_plan, company = resolve_research_plan(research_plan)
    print(f"\nResolved company: {company}")

    evidence = retrieve_research_evidence(
        research_plan=research_plan,
        company=company,
        limit=3,
    )

    print(
        f"\nTotal evidence retrieved: "
        f"{len(evidence)}"
    )

    return synthesize_with_kimi(
        user_question=user_question,
        research_plan=research_plan,
        evidence=evidence,
    )
