import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openrouter import ChatOpenRouter

from models.supervisor import SupervisorPlan
from prompts.supervisor import SUPERVISOR_PROMPT
from tools.company_resolver import resolve_company

load_dotenv()

model = ChatOpenRouter(
    model="z-ai/glm-5.2",
    temperature=0,
    api_key=os.getenv("OPENROUTER_API_KEY"),
    openrouter_provider={"order": ["Baidu Qianfan"]},
).with_structured_output(SupervisorPlan)

def create_supervisor_plan(user_question: str) -> SupervisorPlan:
    return model.invoke(
        [
            SystemMessage(content=SUPERVISOR_PROMPT),
            HumanMessage(content=user_question),
        ]
    )

def resolve_symbol(plan: SupervisorPlan):
    result = resolve_company.invoke(
        {"company_name": plan.company_name}
    )
    print("Resolver result:", result)

    if result["status"] != "success":
        return {
            "status": "error",
            "message": (
                f"I couldn't reliably match "
                f"'{plan.company_name}' "
                "to a company in the stock database. "
                "Please enter the company name exactly "
                "as it is listed."
            ),
        }

    return {
        "status": "success",
        "symbol": result["matches"][0]["symbol"],
    }

def supervise(user_question: str):
    plan = create_supervisor_plan(user_question)
    resolution = resolve_symbol(plan)

    return {
        "user_question": user_question,
        "company_name": plan.company_name,
        "symbol": resolution.get("symbol"),
        "agents": plan.agents,
        "resolution_error": resolution.get("message"),
    }


if __name__ == "__main__":

    question = "hows wipro's financials?"

    result = supervise(question)

    print("\nSupervisor result:")
    print(result)