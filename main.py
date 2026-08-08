"""
Entry point: Command Line Interface
Usage: python main.py
"""
from gemini_agent import DuneGeminiAgent


def main():
    agent = DuneGeminiAgent()
    print("=" * 50)
    print("On-chain Data Analysis Assistant Started (Type 'exit' to quit)")
    print("Example: Analyze the activity of wallet 0x1234...abcd over the past 7 days")
    print("=" * 50)

    while True:
        question = input("\nYou: ").strip()
        if question.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break
        if not question:
            continue

        try:
            answer = agent.ask(question)
        except Exception as e:
            answer = f"Error: {e}"

        print(f"\nAssistant: {answer}")


if __name__ == "__main__":
    main()