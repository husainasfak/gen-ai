from dotenv import load_dotenv
from openai import OpenAI
import requests
import json

load_dotenv()

client = OpenAI()


def weather_tool(location: str) -> str:
    print("🔨 Tool Called: get_weather", location)
    
    url = f"https://wttr.in/{location}?format=%C+%t"
    response = requests.get(url)

    if response.status_code == 200:
        return f"The weather in {location} is {response.text}."
    return "Something went wrong"


system_prompt = """
    You are an helpful AI aegent who is specialized in resolving user query.
    You work on start, plan, action observe mode.
    For the given user query and available tools, plan the step by step execution, based on the planning, select the relevant tool from the available tool. and based on the tool selection you perform an action to call the tool.
    Wait for the observation and based on the observation from the tool call resolve the user query.

    Rules:
    - Always respond in a single JSON object.
    - Always perform one step at a time and wait for next input.
    - The possible steps are: plan, action, observe, final_answer.
    - Carefully follow the structure for each step:
    
    Output Structure:
    {{
        step: "plan" | "action" | "observe" | "final_answer",
        content: "string",          // For "plan" and "final_answer" steps
        tool: "The name of the tool",             // For "action" step
        tool_input: "string",
    }}
    
    Available Tools:
    - weather_tool(location: str) -> str
    
    Example:
    User Query: "What's the weather like in New York City today?"
    Output: {"step":"plan", "content":"The user is interested in weather data of New York City, so I will use the weather tool to get the data."}
    Output: {"step":"plan", "content":"From the available tools, I will use the weather tool to get the weather data of New York City."}
    Output: {"step":"action", "tool":"weather_tool", "tool_input":"New York City"}
    Output: {"step":"observe", "observation":"The weather in New York City today is sunny with a high of 75F and a low of 60F."}
    Output: {"step":"final_answer", "content":"The weather in New York City today is sunny with a high of 75F and a low of 60F."}
"""

available_tools = {
    "weather_tool": {
        "fn": weather_tool,
        "description": "Get the weather information for a given location.",
    }
}

messages = [
    {"role": "system", "content": system_prompt},
]
user_query = input("> ")

messages.append({"role": "user", "content": user_query})
while True:
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=messages,
    )
    parsed_output = json.loads(response.choices[0].message.content)
    print(f"Agent Output: {parsed_output}")
    messages.append({"role": "assistant", "content": json.dumps(parsed_output)})

    step = parsed_output.get("step")
    if step == "plan":
        print(f"{parsed_output.get('content')}")
        continue

    if step == "action":
        tool_name = parsed_output.get("tool")
        tool_input = parsed_output.get("tool_input")
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
        print(f"{parsed_output.get('observation')}")
        continue

    if step == "final_answer":
        print(f"{parsed_output.get('content')}")
        break
