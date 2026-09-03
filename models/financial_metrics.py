from pydantic import BaseModel, Field


class FinancialMetrics(BaseModel):
    revenue_growth: float | None = Field(
        description="Year-over-year revenue growth percentage."
    )

    profit_growth: float | None = Field(
        description="Year-over-year net profit growth percentage."
    )

    operating_margin: float | None = Field(
        description="Operating margin percentage."
    )

    net_margin: float | None = Field(
        description="Net profit margin percentage."
    )

    roe: float | None = Field(
        description="Return on Equity percentage."
    )

    roce: float | None = Field(
        description="Return on Capital Employed percentage."
    )

    roic: float | None = Field(
        description="Return on Invested Capital percentage."
    )

    debt_to_equity: float | None = Field(
        description="Total debt divided by total equity."
    )

    interest_coverage: float | None = Field(
        description="Interest coverage ratio."
    )

    free_cash_flow: float | None = Field(
        description="Free cash flow in the same units as the source financial statements."
    )

    cash_flow_trends: list[dict] = Field(
        description=(
            "Historical annual cash-flow data containing operating cash flow, "
            "free cash flow, and their year-over-year growth."
        )
    )
