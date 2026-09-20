from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langsmith import traceable

from models.stock import StockDetails
from models.financial_metrics import FinancialMetrics
from tools.stock_market import get_stock_details
from tools.financial_metrics import calculate_financial_metrics


class StockState(TypedDict):
    company_name: str
    symbol: str
    stock_data: StockDetails
    financial_metrics: FinancialMetrics


def get_stock_details_node(state: StockState):
    stock = get_stock_details.invoke({
        "stock_name": state["symbol"]
    })
    return {
        "stock_data": stock
    }


def calculate_metrics_node(state: StockState):
    result = calculate_financial_metrics(
        state["stock_data"]
    )

    if result["status"] != "success":
        raise ValueError(
            result.get(
                "reason",
                "Unable to calculate financial metrics."
            )
        )

    metrics = FinancialMetrics(
        **result["metrics"],
        cash_flow_trends=result["cash_flow_trends"],
    )
    print("Financial metrics:", metrics)
    return {
        "financial_metrics": metrics
    }


graph = StateGraph(StockState)

graph.add_node("get_stock_details", get_stock_details_node)
graph.add_node("calculate_metrics", calculate_metrics_node)

graph.add_edge(START,"get_stock_details")
graph.add_edge("get_stock_details","calculate_metrics")
graph.add_edge("calculate_metrics", END)

app = graph.compile()

@traceable(name="Financial Agent")
def financial(company_name: str, symbol: str):
    result = app.invoke({
        "company_name": company_name,
        "symbol": symbol,
    })
    return {
        "stock_data": result["stock_data"],
        "financial_metrics": result["financial_metrics"],
    }