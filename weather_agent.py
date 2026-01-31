from dotenv import load_dotenv
import json
from typing import Optional
from urllib.parse import quote

from openai import OpenAI
from pydantic import BaseModel, Field
import requests

load_dotenv()

client = OpenAI()


def weather_tool(location: str) -> str:
    print("Tool Called: get_weather", location)

    safe_location = quote(location.strip())
    url = f"https://wttr.in/{safe_location}?format=%C+%t"
    try:
        response = requests.get(url, timeout=10)
    except requests.RequestException as exc:
        return f"Weather lookup failed: {exc}"

    if response.status_code == 200:
        return f"The weather in {location} is {response.text}."
    return f"Weather lookup failed with status {response.status_code}."


system_prompt = """
You are a helpful AI agent specialized in resolving user queries.
You operate in plan, action, observe, final_answer steps.
For the given user query and available tools, plan the step-by-step execution.
Based on the plan, select the relevant tool and perform an action to call it.
Wait for the observation and, based on that, resolve the user query.

Rules:
- Always respond in a single JSON object.
- Always perform one step at a time and wait for next input.
- The possible steps are: plan, action, observe, final_answer.
- Follow the structure for each step.

Output Structure:
{
  "step": "plan" | "action" | "observe" | "final_answer",
  "content": "string",          // For "plan" and "final_answer" steps
  "tool": "The name of the tool",             // For "action" step
  "tool_input": "string",        // For "action" step
  "observation": "string"        // For "observe" step
}

Available Tools:
- weather_tool(location: str) -> str

Example:
User Query: "What's the weather like in New York City today?"
Output: {"step":"plan","content":"The user wants weather data, so I will call the weather tool."}
Output: {"step":"action","tool":"weather_tool","tool_input":"New York City"}
Output: {"step":"observe","observation":"The weather in New York City is Sunny +75F."}
Output: {"step":"final_answer","content":"The weather in New York City is Sunny +75F."}
""".strip()

available_tools = {
    "weather_tool": {
        "fn": weather_tool,
        "description": "Get the weather information for a given location.",
    }
}


class OutputFormat(BaseModel):
    step: str = Field(..., description="The current step in the agent's process.")
    content: Optional[str] = Field(None, description="Content for 'plan' and 'final_answer' steps.")
    tool: Optional[str] = Field(None, description="The name of the tool to be used in 'action' step.")
    tool_input: Optional[str] = Field(None, description="Input for the tool in 'action' step.")
    observation: Optional[str] = Field(None, description="Observation from the tool in 'observe' step.")


messages = [{"role": "system", "content": system_prompt}]
user_query = input("> ").strip()
messages.append({"role": "user", "content": user_query})

while True:
    response = client.chat.completions.parse(
        model="gpt-4o",
        response_format=OutputFormat,
        messages=messages,
    )
    parsed_output = response.choices[0].message.parsed
    parsed_dict = parsed_output.model_dump()

    print(f"Agent Output: {parsed_dict}")
    messages.append({"role": "assistant", "content": json.dumps(parsed_dict)})

    step = parsed_output.step
    if step == "plan":
        print(parsed_output.content or "")
        continue

    if step == "action":
        tool_name = parsed_output.tool or ""
        tool_input = parsed_output.tool_input or ""
        if tool_name in available_tools:
            observation = available_tools[tool_name]["fn"](tool_input)
        else:
            observation = f"Tool '{tool_name}' not found."
        print(f"Observation: {observation}")
        messages.append(
            {"role": "assistant", "content": json.dumps({"step": "observe", "observation": observation})}
        )
        continue

    if step == "observe":
        print(parsed_output.observation or "")
        continue

    if step == "final_answer":
        print(parsed_output.content or "")
        break
