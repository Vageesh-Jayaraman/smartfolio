import os

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openrouter import ChatOpenRouter
from langgraph.graph import MessagesState, StateGraph, START, END
from pydantic import BaseModel, Field

from tools.company_resolver import resolve_company
from tools.stock_market import get_stock_details
from models.stock import StockDetails


load_dotenv()


model = ChatOpenRouter(
    model="z-ai/glm-5.2",
    temperature=0,
    api_key=os.getenv("OPENROUTER_API_KEY"),
    openrouter_provider={"order": ["Baidu Qianfan"]},
)


class CompanyQuery(BaseModel):
    company_name: str = Field(
        description=(
            "Extract only the company name explicitly mentioned by the user. "
            "Do not use outside knowledge. "
            "Do not infer, correct, rename, expand, or substitute the company name. "
            "Preserve the company name as the user provided it."
        )
    )


company_model = model.with_structured_output(CompanyQuery)


class StockState(MessagesState):
    company_name: str
    symbol: str
    stock_data: StockDetails
    resolution_error: str


def extract_company(state: StockState):
    result = company_model.invoke(state["messages"])
    print("LLM extracted:", repr(result.company_name))
    return {
        "company_name": result.company_name
    }


def resolve_symbol_node(state: StockState):
    result = resolve_company.invoke({
        "company_name": state["company_name"]
    })
    print("Resolver result:", result)

    if result["status"] != "success":
        return {
            "resolution_error": (
                f"I couldn't reliably match '{state['company_name']}' "
                "to a company in the stock database. "
                "Please enter the company name exactly as it is listed."
            )
        }

    return {
        "symbol": result["matches"][0]["symbol"]
    }


def resolution_router(state: StockState):
    if "resolution_error" in state:
        return "ask_user"

    return "get_stock_details"


def ask_user(state: StockState):
    return {
        "messages": [
            {
                "role": "assistant",
                "content": state["resolution_error"]
            }
        ]
    }


def get_stock_details_node(state: StockState):
    stock = get_stock_details.invoke({
        "stock_name": state["symbol"]
    })
    return {
        "stock_data": stock
    }


def analyze_stock(state: StockState):
    stock_data = state["stock_data"]

    response = model.invoke([
        *state["messages"],
        SystemMessage(
            content=(
                "You are a financial analyst. "
                "Analyze only the stock data provided below and answer "
                "the user's original question.\n\n"
                f"Stock data:\n{stock_data.model_dump_json(indent=2)}"
            )
        ),
    ])

    return {
        "messages": [response]
    }


graph = StateGraph(StockState)

graph.add_node("extract_company",extract_company)
graph.add_node("resolve_company",resolve_symbol_node)
graph.add_node("get_stock_details",get_stock_details_node)
graph.add_node("analyze_stock",analyze_stock)
graph.add_node("ask_user",ask_user)

graph.add_edge(START,"extract_company")
graph.add_edge("extract_company","resolve_company")

graph.add_conditional_edges(
    "resolve_company",
    resolution_router,
    {
        "get_stock_details": "get_stock_details",
        "ask_user": "ask_user",
    },
)

graph.add_edge("get_stock_details","analyze_stock")
graph.add_edge("analyze_stock",END)
graph.add_edge("ask_user",END)

app = graph.compile()