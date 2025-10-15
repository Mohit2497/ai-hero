from . import ingest
from . import search_agent
from . import logs

import asyncio

REPO_OWNER = "microsoft"
REPO_NAME = "ai-agents-for-beginners"

def initialize_index():
    print(f"Starting AI Assistant for {REPO_OWNER}/{REPO_NAME}")
    print("Initializing data ingestion...")

    # Optional filter function to include only specific files
    # def filter(doc):
    #     return "data-engineering" in doc["filename"]

    index = ingest.index_data(REPO_OWNER, REPO_NAME, filter=None)
    print("Data indexing completed successfully!")

    return index


def initialize_agent(index):
    print("Initializing search agent...")
    agent = search_agent.init_agent(index, REPO_OWNER, REPO_NAME)
    print("Agent initialized successfully!")

    return agent


async def ask_question(agent, question):
    """Async function to handle a single question"""
    print("Processing your question...")
    response = await agent.run(user_prompt=question)
    logs.log_interaction_to_file(agent, response.new_messages())
    return response.output


async def main_async():
    """Main async function to handle the conversation loop"""
    index = initialize_index()
    agent = initialize_agent(index)
    print("\nReady to answer your questions!")
    print("Type 'stop' to exit the program.\n")

    while True:
        question = input("Your question: ")
        if question.strip().lower() == "stop":
            print("Goodbye!")
            break

        try:
            response_output = await ask_question(agent, question)
            print("\nResponse:\n", response_output)
            print("\n" + "=" * 50 + "\n")
        except Exception as e:
            print(f"Error processing question: {e}")
            print("Please try again.\n")


def main():
    """Entry point that runs the async main function"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()