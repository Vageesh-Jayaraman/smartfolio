from concurrent.futures import ThreadPoolExecutor, as_completed

from agents.supervisor import supervise
from agents.financial_agent import financial
from agents.research_agent import research
from agents.news_agent import research_news
from agents.final_analyst import analyze


def run(user_question: str):

    print("\nRunning supervisor...")
    plan = supervise(user_question)

    if plan["resolution_error"]:
        return plan["resolution_error"]

    company_name = plan["company_name"]
    symbol = plan["symbol"]
    agents = [agent.value for agent in plan["agents"]]

    print(f"\nCompany: {company_name}")
    print(f"Symbol: {symbol}")
    print(f"Agents: {agents}")

    results = {
        "financial": None,
        "research": None,
        "news": None,
    }

    futures = {}

    with ThreadPoolExecutor(max_workers=3) as executor:

        if "financial" in agents:
            print("\nStarting financial agent...")
            futures["financial"] = executor.submit(
                financial,
                company_name=company_name,
                symbol=symbol,
            )

        if "research" in agents:
            print("\nStarting research agent...")
            futures["research"] = executor.submit(
                research,
                user_question=user_question,
                company_name=company_name,
                symbol=symbol,
            )

        if "news" in agents:
            print("\nStarting news agent...")
            futures["news"] = executor.submit(
                research_news,
                user_question=user_question,
                company_name=company_name,
                symbol=symbol,
            )

        for agent_name, future in futures.items():
            results[agent_name] = future.result()

    print("\nRunning final analyst...")

    answer = analyze(
        user_question=user_question,
        company_name=company_name,
        symbol=symbol,
        financial=results["financial"],
        research=results["research"],
        news=results["news"],
    )

    return answer


if __name__ == "__main__":

    question = input(
        "What would you like to know? "
    )

    answer = run(question)

    print("\n" + "=" * 80)
    print("FINAL ANSWER")
    print("=" * 80)
    print(answer)