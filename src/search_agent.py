"""
Module to initialize and configure the search agent.
"""

import os
import logging
from dotenv import load_dotenv
from pydantic_ai import Agent
from app import search_tools

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


SYSTEM_PROMPT_TEMPLATE = """
You are an AI assistant specialized in Microsoft's AI Agents documentation from the ai-agents-for-beginners repository.

CRITICAL INSTRUCTIONS:
1. YOU MUST ALWAYS USE THE SEARCH TOOL for EVERY question, even if you think you know the answer
2. NEVER provide answers without searching the documentation first
3. If a question seems unrelated to AI agents, still search to find any relevant connections
4. Always base your response on search results, not on general knowledge

Search Process:
- For technical questions: search for specific terms, APIs, or concepts
- For general questions: search for related topics in the documentation
- If first search returns no results, try alternative search terms

Response Format:
1. Start by searching for relevant information
2. Provide specific, accurate answers from the documentation
3. Include citations by mentioning the source file: [filename](github_link)
4. If no relevant information found, state this clearly

Remember: EVERY response must be based on search results from the documentation.
Format citations as: [LINK TITLE](FULL_GITHUB_LINK)
"""

def init_agent(index, repo_owner: str, repo_name: str) -> Agent:
    """
    Initialize the search agent with the given index and repository information.
    """
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        repo_owner=repo_owner, repo_name=repo_name
    )

    search_tool = search_tools.SearchTool(index=index)

    agent = Agent(
        name="Repo_Assistant_V2",
        instructions=system_prompt,
        tools=[search_tool.search],
        model="gemini-2.5-flash",
    )

    return agent