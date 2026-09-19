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

    financial_result = None
    research_result = None
    news_result = None

    if "financial" in agents:
        print("\nRunning financial agent...")

        financial_result = financial(
            company_name=company_name,
            symbol=symbol,
        )

    if "research" in agents:
        print("\nRunning research agent...")

        research_result = research(
            user_question=user_question,
            company_name=company_name,
            symbol=symbol,
        )

    if "news" in agents:
        print("\nRunning news agent...")

        news_result = research_news(
            user_question=user_question,
            company_name=company_name,
            symbol=symbol,
        )

    print("\nRunning final analyst...")

    answer = analyze(
        user_question=user_question,
        company_name=company_name,
        symbol=symbol,
        financial=financial_result,
        research=research_result,
        news=news_result,
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