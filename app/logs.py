import json
import os
import secrets
from datetime import date, datetime
from pathlib import Path

from pydantic_ai.messages import ModelMessagesTypeAdapter

LOG_DIR = Path(os.getenv("LOGS_DIRECTORY", "logs"))
LOG_DIR.mkdir(exist_ok=True)


def log_entry(agent, messages, source="user"):
    """ "
    Create a log entry dictionary capturing the agent interaction details.

    Args:
        agent: The agent instance.
        messages: The list of message objects exchanged with the agent.
        source (str): The source of the interaction, e.g., "user" or "system".

    Returns:
        dict: A dictionary representing the log entry.
    """
    tools = []

    for ts in agent.toolsets:
        tools.extend(ts.tools.keys())

    dict_messages = ModelMessagesTypeAdapter.dump_python(messages)

    return {
        "agent_name": agent.name,
        "system_prompt": agent._instructions,
        "provider": agent.model.system,
        "model": agent.model.model_name,
        "tools": tools,
        "messages": dict_messages,
        "source": source,
    }


def serializer(obj):
    """ "
    JSON serializer for objects not serializable by default.
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def log_interaction_to_file(agent, messages, source="user"):
    """ "
    Log the agent interaction to a JSON file in the LOG_DIR directory.

    Args:
        agent: The agent instance.
        messages: The list of message objects exchanged with the agent.
        source (str): The source of the interaction, e.g., "user" or "system".

    Returns:
        Path: The file path of the logged interaction.
    """
    entry = log_entry(agent, messages, source)

    ts = entry["messages"][-1]["timestamp"]
    ts_str = ts.strftime("%Y%m%d_%H%M%S")
    rand_hex = secrets.token_hex(3)

    filename = f"{agent.name}_{ts_str}_{rand_hex}.json"
    filepath = LOG_DIR / filename

    with filepath.open("w", encoding="utf-8") as f_out:
        json.dump(entry, f_out, indent=2, default=serializer)

    return filepath