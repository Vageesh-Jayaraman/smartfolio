import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from agents.final_analyst import analyze
from agents.financial_agent import financial
from agents.news_agent import research_news
from agents.research_agent import research
from agents.supervisor import supervise

RESET = "\033[0m"
BLUE = "\033[94m"
GREEN = "\033[92m"
MAGENTA = "\033[95m"
RED = "\033[91m"
YELLOW = "\033[93m"

def run(user_question: str):
    print(f"{BLUE}Running supervisor...{RESET}")

    plan = supervise(user_question)

    if plan["resolution_error"]:
        print(f"{RED}{plan['resolution_error']}{RESET}")
        return plan["resolution_error"]

    company_name = plan["company_name"]
    symbol = plan["symbol"]
    agents = [agent.value for agent in plan["agents"]]

    print(f"{MAGENTA}Company: {company_name}{RESET}")
    print(f"{MAGENTA}Symbol: {symbol}{RESET}")
    print(f"{MAGENTA}Agents: {agents}{RESET}")

    results = {
        "financial": None,
        "research": None,
        "news": None,
    }

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}

        if "financial" in agents:
            print(f"{YELLOW}Starting financial agent...{RESET}")

            futures["financial"] = executor.submit(
                financial,
                company_name=company_name,
                symbol=symbol,
            )

        if "research" in agents:
            print(f"{YELLOW}Starting research agent...{RESET}")

            futures["research"] = executor.submit(
                research,
                user_question=user_question,
                company_name=company_name,
                symbol=symbol,
            )

        if "news" in agents:
            print(f"{YELLOW}Starting news agent...{RESET}")

            futures["news"] = executor.submit(
                research_news,
                user_question=user_question,
                company_name=company_name,
                symbol=symbol,
            )

        for agent_name, future in futures.items():
            results[agent_name] = future.result()

    print(f"{BLUE}Running final analyst...{RESET}")

    answer = analyze(
        user_question=user_question,
        company_name=company_name,
        symbol=symbol,
        financial=results["financial"],
        research=results["research"],
        news=results["news"],
    )

    return answer


def main():
    parser = argparse.ArgumentParser(
        prog="smartfolio",
        description="AI-assisted equity research.",
    )

    parser.add_argument(
        "question",
        help="Research question about a company.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Save the answer to a file.",
    )

    args = parser.parse_args()

    try:
        answer = run(args.question)

    except KeyboardInterrupt:
        print(f"\n{YELLOW}Research cancelled.{RESET}")
        return

    except Exception as error:
        print(f"{RED}SmartFolio failed: {error}{RESET}")
        return

    print(f"\n{GREEN}{answer}{RESET}")

    if args.output:
        args.output.write_text(
            answer + "\n",
            encoding="utf-8",
            )

if __name__ == "__main__":
    main()