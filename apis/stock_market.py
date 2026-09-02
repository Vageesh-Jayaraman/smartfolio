import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

from models.stock import StockDetails

load_dotenv()

API_KEY = os.getenv("INDIAN_API_KEY")
BASE_URL = "https://stock.indianapi.in"


@tool
def get_stock_details(stock_name: str) -> StockDetails:
    """
    Fetch stock details from Indian Stock Exchange API.

    Args:
        stock_name: Company name or stock search term.
                    Example: "Reliance", "TCS", "Infosys"

    Returns:
        Structured stock details.
    """

    if not API_KEY:
        raise ValueError("INDIAN_API_KEY not found in environment variables.")

    response = requests.get(
        f"{BASE_URL}/stock",
        headers={
            "X-Api-Key": API_KEY
        },
        params={
            "name": stock_name
        },
        timeout=10
    )

    response.raise_for_status()
    stock = StockDetails.model_validate(response.json())

    print(stock)
    return stock