from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os
from langchain_openrouter import ChatOpenRouter

from apis.stock_market import get_stock_details

load_dotenv()

model = ChatOpenRouter(
    model="z-ai/glm-5.2",
    temperature=0,
    api_key= os.getenv("OPENROUTER_API_KEY"),
    openrouter_provider={"order": ["Baidu Qianfan"]}
)

model.bind_tools([get_stock_details])
