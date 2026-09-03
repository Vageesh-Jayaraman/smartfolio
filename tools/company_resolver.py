from functools import lru_cache
import re
from pathlib import Path

import pandas as pd
from rapidfuzz import process
from rapidfuzz.distance import JaroWinkler
from langchain_core.tools import tool


CSV_PATH = Path(__file__).resolve().parents[1] / "docs" / "EQUITY_L.csv"

FUZZY_THRESHOLD = 0.80
MAX_MATCHES = 5


def normalize_name(name: str) -> str:
    name = name.lower()

    name = re.sub(
        r"\b(limited|ltd|private|pvt|corporation|corp|inc)\b",
        "",
        name,
    )

    name = re.sub(r"[^a-z0-9\s]", " ", name)
    name = re.sub(r"\s+", " ", name)

    return name.strip()


def normalize_symbol(symbol: str) -> str:
    return re.sub(
        r"[^a-z0-9]",
        "",
        symbol.lower(),
    )


@lru_cache(maxsize=1)
def load_companies() -> pd.DataFrame:
    print("Loading EQUITY_L.csv...")

    companies = pd.read_csv(
        CSV_PATH,
        skipinitialspace=True,
    )

    companies.columns = companies.columns.str.strip()

    required_columns = {
        "SYMBOL",
        "NAME OF COMPANY",
    }

    missing_columns = required_columns - set(companies.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"Missing required columns in EQUITY_L.csv: {missing}"
        )

    companies = companies.dropna(
        subset=["SYMBOL", "NAME OF COMPANY"]
    ).copy()

    companies["normalized_name"] = companies[
        "NAME OF COMPANY"
    ].astype(str).apply(normalize_name)

    companies["normalized_symbol"] = companies[
        "SYMBOL"
    ].astype(str).apply(normalize_symbol)

    return companies.reset_index(drop=True)


def create_match(
        row: pd.Series,
        score: float,
        match_type: str,
) -> dict:
    return {
        "symbol": row["SYMBOL"],
        "company_name": row["NAME OF COMPANY"],
        "score": round(score * 100, 2),
        "match_type": match_type,
    }


def find_exact_company_match(
        companies: pd.DataFrame,
        query: str,
) -> list[dict]:

    matches = companies[
        companies["normalized_name"] == query
        ]

    return [
        create_match(
            row,
            1.0,
            "exact_company_name",
        )
        for _, row in matches.iterrows()
    ]


def find_exact_symbol_match(
        companies: pd.DataFrame,
        query: str,
) -> list[dict]:

    matches = companies[
        companies["normalized_symbol"] == query
        ]

    return [
        create_match(
            row,
            1.0,
            "exact_symbol",
        )
        for _, row in matches.iterrows()
    ]


def find_fuzzy_company_matches(
        companies: pd.DataFrame,
        query: str,
) -> list[dict]:

    results = process.extract(
        query,
        companies["normalized_name"].tolist(),
        scorer=JaroWinkler.normalized_similarity,
        limit=MAX_MATCHES,
    )

    matches = []

    for _, score, index in results:
        if score < FUZZY_THRESHOLD:
            continue

        row = companies.iloc[index]

        matches.append(
            create_match(
                row,
                score,
                "fuzzy_company_name",
            )
        )

    return matches


def remove_duplicate_symbols(
        matches: list[dict],
) -> list[dict]:

    unique_matches = []
    seen_symbols = set()

    for match in matches:
        symbol = match["symbol"]

        if symbol in seen_symbols:
            continue

        seen_symbols.add(symbol)
        unique_matches.append(match)

    return unique_matches


def sort_matches(
        matches: list[dict],
) -> list[dict]:

    return sorted(
        matches,
        key=lambda match: match["score"],
        reverse=True,
    )


def resolve_fuzzy_matches(
        matches: list[dict],
) -> dict:

    if not matches:
        return {
            "status": "not_found",
            "matches": [],
        }

    best_match = sort_matches(matches)[0]

    return {
        "status": "success",
        "matches": [best_match],
    }


@tool
def resolve_company(company_name: str) -> dict:
    """
    Resolve a company name or stock symbol to an NSE symbol.
    Exact matches are preferred. Otherwise, the highest-scoring
    fuzzy company-name match is returned if it passes the threshold.
    """

    company_query = normalize_name(company_name)

    if not company_query:
        return {
            "status": "not_found",
            "matches": [],
        }

    companies = load_companies()

    exact_company_matches = find_exact_company_match(
        companies,
        company_query,
    )

    if exact_company_matches:
        return {
            "status": "success",
            "matches": exact_company_matches,
        }

    symbol_query = normalize_symbol(company_name)

    exact_symbol_matches = find_exact_symbol_match(
        companies,
        symbol_query,
    )

    if exact_symbol_matches:
        return {
            "status": "success",
            "matches": exact_symbol_matches,
        }

    fuzzy_matches = find_fuzzy_company_matches(
        companies,
        company_query,
    )

    fuzzy_matches = remove_duplicate_symbols(
        fuzzy_matches
    )

    return resolve_fuzzy_matches(
        fuzzy_matches
    )