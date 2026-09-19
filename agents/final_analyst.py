import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openrouter import ChatOpenRouter

from prompts.final_analyst import FINAL_ANALYST_PROMPT

load_dotenv()

analyst_model = ChatOpenRouter(
    model="z-ai/glm-5.2",
    temperature=0,
    api_key=os.getenv("OPENROUTER_API_KEY"),
    openrouter_provider={"order": ["Baidu Qianfan"]},
)


def format_financial_data(financial):
    if not financial:
        return ""

    return f"""
            FINANCIAL EVIDENCE:
            
            Stock Data:
            {financial.get("stock_data")}
            
            Financial Metrics:
            {financial.get("financial_metrics")}
            """

def format_research_evidence(evidence):
    if not evidence:
        return ""

    formatted = []

    for i, item in enumerate(evidence):
        result = item["result"]
        payload = result.payload
        metadata = payload["metadata"]

        formatted.append(
            f"""
            [R{i}]
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

    return "RESEARCH EVIDENCE:\n" + "\n".join(formatted)

def format_news_evidence(evidence):
    if not evidence:
        return ""

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
            
            Content:
            {result.get("content", "")}
            """
        )

    return "NEWS EVIDENCE:\n" + "\n".join(formatted)


def analyze(
        user_question: str,
        company_name: str,
        symbol: str,
        financial=None,
        research=None,
        news=None,
):

    evidence = []

    financial_text = format_financial_data(financial)
    research_text = format_research_evidence(research)
    news_text = format_news_evidence(news)

    if financial_text:
        evidence.append(financial_text)

    if research_text:
        evidence.append(research_text)

    if news_text:
        evidence.append(news_text)

    evidence_text = "\n\n".join(evidence)

    response = analyst_model.invoke(
        [
            SystemMessage(content=FINAL_ANALYST_PROMPT),
            HumanMessage(
                content=(
                    f"USER QUESTION:\n"
                    f"{user_question}\n\n"
                    f"COMPANY:\n"
                    f"{company_name}\n\n"
                    f"SYMBOL:\n"
                    f"{symbol}\n\n"
                    f"{evidence_text}"
                )
            ),
        ]
    )

    return response.content