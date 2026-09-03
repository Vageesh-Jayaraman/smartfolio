from typing import Optional

from models.stock import FinancialPeriod, StockDetails


def _statement_to_dict(items) -> dict[str, float]:
    values = {}

    for item in items:
        if item.value is None:
            continue

        try:
            values[item.key] = float(item.value)
        except (TypeError, ValueError):
            continue

    return values


def _get_period_data(period: FinancialPeriod) -> dict[str, dict[str, float]]:
    financial_map = period.stockFinancialMap

    return {
        "INC": _statement_to_dict(financial_map.INC),
        "BAL": _statement_to_dict(financial_map.BAL),
        "CAS": _statement_to_dict(financial_map.CAS),
    }


def _get_value(
        period_data: dict[str, dict[str, float]],
        statement: str,
        key: str,
) -> Optional[float]:
    return period_data.get(statement, {}).get(key)


def _safe_divide(
        numerator: Optional[float],
        denominator: Optional[float],
) -> Optional[float]:
    if numerator is None or denominator is None:
        return None

    if denominator == 0:
        return None

    return numerator / denominator


def _percentage_change(
        current: Optional[float],
        previous: Optional[float],
) -> Optional[float]:
    if current is None or previous is None:
        return None

    if previous == 0:
        return None

    return ((current - previous) / abs(previous)) * 100


def _average(
        current: Optional[float],
        previous: Optional[float],
) -> Optional[float]:
    if current is None or previous is None:
        return None

    return (current + previous) / 2


def _sort_annual_periods(
        stock: StockDetails,
) -> list[FinancialPeriod]:
    periods = [
        period
        for period in stock.financials
        if period.Type.lower() == "annual"
    ]

    return sorted(
        periods,
        key=lambda period: period.EndDate,
        reverse=True,
    )


def calculate_revenue_growth(
        current: dict[str, dict[str, float]],
        previous: dict[str, dict[str, float]],
) -> Optional[float]:
    current_revenue = _get_value(current, "INC", "Revenue")
    previous_revenue = _get_value(previous, "INC", "Revenue")

    return _percentage_change(
        current_revenue,
        previous_revenue,
    )


def calculate_profit_growth(
        current: dict[str, dict[str, float]],
        previous: dict[str, dict[str, float]],
) -> Optional[float]:
    current_profit = _get_value(current, "INC", "NetIncome")
    previous_profit = _get_value(previous, "INC", "NetIncome")

    return _percentage_change(
        current_profit,
        previous_profit,
    )


def calculate_operating_margin(
        current: dict[str, dict[str, float]],
) -> Optional[float]:
    operating_income = _get_value(
        current,
        "INC",
        "OperatingIncome",
    )

    revenue = _get_value(
        current,
        "INC",
        "Revenue",
    )

    result = _safe_divide(
        operating_income,
        revenue,
    )

    return result * 100 if result is not None else None


def calculate_net_margin(
        current: dict[str, dict[str, float]],
) -> Optional[float]:
    net_income = _get_value(
        current,
        "INC",
        "NetIncome",
    )

    revenue = _get_value(
        current,
        "INC",
        "Revenue",
    )

    result = _safe_divide(
        net_income,
        revenue,
    )

    return result * 100 if result is not None else None


def calculate_roe(
        current: dict[str, dict[str, float]],
        previous: Optional[dict[str, dict[str, float]]] = None,
) -> Optional[float]:
    net_income = _get_value(
        current,
        "INC",
        "NetIncome",
    )

    current_equity = _get_value(
        current,
        "BAL",
        "TotalEquity",
    )

    previous_equity = (
        _get_value(previous, "BAL", "TotalEquity")
        if previous is not None
        else None
    )

    if previous_equity is not None:
        equity = _average(
            current_equity,
            previous_equity,
        )
    else:
        equity = current_equity

    result = _safe_divide(
        net_income,
        equity,
    )

    return result * 100 if result is not None else None


def calculate_roce(
        current: dict[str, dict[str, float]],
        previous: Optional[dict[str, dict[str, float]]] = None,
) -> Optional[float]:
    operating_income = _get_value(
        current,
        "INC",
        "OperatingIncome",
    )

    current_assets = _get_value(
        current,
        "BAL",
        "TotalAssets",
    )

    current_liabilities = _get_value(
        current,
        "BAL",
        "TotalCurrentLiabilities",
    )

    current_capital_employed = (
        current_assets - current_liabilities
        if current_assets is not None
           and current_liabilities is not None
        else None
    )

    previous_capital_employed = None

    if previous is not None:
        previous_assets = _get_value(
            previous,
            "BAL",
            "TotalAssets",
        )

        previous_liabilities = _get_value(
            previous,
            "BAL",
            "TotalCurrentLiabilities",
        )

        if (
                previous_assets is not None
                and previous_liabilities is not None
        ):
            previous_capital_employed = (
                    previous_assets - previous_liabilities
            )

    if previous_capital_employed is not None:
        capital_employed = _average(
            current_capital_employed,
            previous_capital_employed,
        )
    else:
        capital_employed = current_capital_employed

    result = _safe_divide(
        operating_income,
        capital_employed,
    )

    return result * 100 if result is not None else None


def calculate_roic(
        current: dict[str, dict[str, float]],
        previous: Optional[dict[str, dict[str, float]]] = None,
) -> Optional[float]:
    operating_income = _get_value(
        current,
        "INC",
        "OperatingIncome",
    )

    tax_expense = _get_value(
        current,
        "INC",
        "ProvisionforIncomeTaxes",
    )

    pre_tax_income = _get_value(
        current,
        "INC",
        "NetIncomeBeforeTaxes",
    )

    if (
            operating_income is None
            or tax_expense is None
            or pre_tax_income is None
            or pre_tax_income == 0
    ):
        return None

    tax_rate = tax_expense / pre_tax_income
    nopat = operating_income * (1 - tax_rate)

    debt = _get_value(
        current,
        "BAL",
        "TotalDebt",
    )

    equity = _get_value(
        current,
        "BAL",
        "TotalEquity",
    )

    cash = _get_value(
        current,
        "BAL",
        "Cash",
    )

    if debt is None or equity is None or cash is None:
        return None

    invested_capital = debt + equity - cash

    previous_invested_capital = None

    if previous is not None:
        previous_debt = _get_value(
            previous,
            "BAL",
            "TotalDebt",
        )

        previous_equity = _get_value(
            previous,
            "BAL",
            "TotalEquity",
        )

        previous_cash = _get_value(
            previous,
            "BAL",
            "Cash",
        )

        if (
                previous_debt is not None
                and previous_equity is not None
                and previous_cash is not None
        ):
            previous_invested_capital = (
                    previous_debt
                    + previous_equity
                    - previous_cash
            )

    if previous_invested_capital is not None:
        invested_capital = _average(
            invested_capital,
            previous_invested_capital,
        )

    result = _safe_divide(
        nopat,
        invested_capital,
    )

    return result * 100 if result is not None else None


def calculate_debt_to_equity(
        current: dict[str, dict[str, float]],
) -> Optional[float]:
    debt = _get_value(
        current,
        "BAL",
        "TotalDebt",
    )

    equity = _get_value(
        current,
        "BAL",
        "TotalEquity",
    )

    return _safe_divide(
        debt,
        equity,
    )


def calculate_interest_coverage(
        current: dict[str, dict[str, float]],
) -> Optional[float]:
    operating_income = _get_value(
        current,
        "INC",
        "OperatingIncome",
    )

    interest_paid = _get_value(
        current,
        "CAS",
        "CashInterestPaid",
    )

    if interest_paid is None:
        return None

    interest_expense = abs(interest_paid)

    return _safe_divide(
        operating_income,
        interest_expense,
    )


def calculate_free_cash_flow(
        current: dict[str, dict[str, float]],
) -> Optional[float]:
    operating_cash_flow = _get_value(
        current,
        "CAS",
        "CashfromOperatingActivities",
    )

    capital_expenditures = _get_value(
        current,
        "CAS",
        "CapitalExpenditures",
    )

    if operating_cash_flow is None or capital_expenditures is None:
        return None

    return operating_cash_flow + capital_expenditures


def calculate_cash_flow_trends(
        periods: list[tuple[FinancialPeriod, dict[str, dict[str, float]]]],
) -> list[dict]:
    trends = []

    for index, (period, current) in enumerate(periods):
        operating_cash_flow = _get_value(
            current,
            "CAS",
            "CashfromOperatingActivities",
        )

        free_cash_flow = calculate_free_cash_flow(current)

        previous = (
            periods[index + 1][1]
            if index + 1 < len(periods)
            else None
        )

        previous_operating_cash_flow = (
            _get_value(
                previous,
                "CAS",
                "CashfromOperatingActivities",
            )
            if previous is not None
            else None
        )

        previous_free_cash_flow = (
            calculate_free_cash_flow(previous)
            if previous is not None
            else None
        )

        trends.append(
            {
                "fiscal_year": period.FiscalYear,
                "end_date": period.EndDate,
                "operating_cash_flow": operating_cash_flow,
                "free_cash_flow": free_cash_flow,
                "operating_cash_flow_growth": _percentage_change(
                    operating_cash_flow,
                    previous_operating_cash_flow,
                ),
                "free_cash_flow_growth": _percentage_change(
                    free_cash_flow,
                    previous_free_cash_flow,
                ),
            }
        )

    return trends


def calculate_financial_metrics(
        stock: StockDetails,
) -> dict:
    periods = _sort_annual_periods(stock)

    if not periods:
        return {
            "company_name": stock.companyName,
            "status": "unavailable",
            "reason": "No annual financial data available.",
            "metrics": {},
            "cash_flow_trends": [],
        }

    current_period = periods[0]
    current_data = _get_period_data(current_period)

    previous_period = periods[1] if len(periods) > 1 else None
    previous_data = (
        _get_period_data(previous_period)
        if previous_period is not None
        else None
    )

    metric_values = {
        "revenue_growth": calculate_revenue_growth(
            current_data,
            previous_data,
        ) if previous_data is not None else None,

        "profit_growth": calculate_profit_growth(
            current_data,
            previous_data,
        ) if previous_data is not None else None,

        "operating_margin": calculate_operating_margin(
            current_data,
        ),

        "net_margin": calculate_net_margin(
            current_data,
        ),

        "roe": calculate_roe(
            current_data,
            previous_data,
        ),

        "roce": calculate_roce(
            current_data,
            previous_data,
        ),

        "roic": calculate_roic(
            current_data,
            previous_data,
        ),

        "debt_to_equity": calculate_debt_to_equity(
            current_data,
        ),

        "interest_coverage": calculate_interest_coverage(
            current_data,
        ),

        "free_cash_flow": calculate_free_cash_flow(
            current_data,
        ),
    }

    trend_periods = [
        (period, _get_period_data(period))
        for period in periods
    ]

    return {
        "company_name": stock.companyName,
        "status": "success",
        "period": {
            "fiscal_year": current_period.FiscalYear,
            "end_date": current_period.EndDate,
        },
        "metrics": metric_values,
        "cash_flow_trends": calculate_cash_flow_trends(
            trend_periods,
        ),
    }

