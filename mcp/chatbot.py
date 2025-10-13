import os
import asyncio
import json
import google.generativeai as genai
from fastmcp import Client
from crewai import Agent
from dotenv import load_dotenv
import re

# --- Load environment variables ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in .env")

# --- Configure Gemini ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# --- Define a CrewAI Agent (no MCP client inside) ---
agent = Agent(
    name="Rental Agent",
    role="Helps tenants and landlords interact with the RentalAgreement smart contract",
    goal="Interpret user requests and call the correct MCP tools to manage the contract",
    backstory="You are connected to an MCP server that exposes blockchain smart contract tools. "
              "Your job is to listen to the user, decide which tool to call, "
              "and return the blockchain transaction result."
)

# --- Ask Gemini which tool to call ---
async def decide_tool(user_input: str, tools: list) -> dict:
    tool_descriptions = "\n".join([f"- {t.name}: {t.description}" for t in tools])
    prompt = f"""
You are an AI agent managing a rental contract.

Available tools:
{tool_descriptions}

User request: "{user_input}"

Respond with **valid JSON only**.
Do not include code fences, explanations, or any extra text.
Output must look exactly like:
{{ "tool": "tool_name", "args": {{ ... }} }}
"""
    response = model.generate_content(prompt)
    response_text = response.text.strip()

    # remove markdown fences if present
    if response_text.startswith("```"):
        response_text = re.sub(r"^```(json)?", "", response_text)
        response_text = re.sub(r"```$", "", response_text).strip()

    try:
        return json.loads(response_text)
    except Exception as e:
        return {"error": f"Invalid JSON from Gemini: {response_text}", "exception": str(e)}

# --- Main chat loop ---
async def main():
    client = Client("./smart_contract_server.py")  # MCP client
    async with client:
        tools = await client.list_tools()
        print("Rental Agreement Chatbot (CrewAI + Gemini + MCP)")
        print("Type 'quit' to exit.\n")

        while True:
            user_input = input("You: ")
            if user_input.lower() in ["quit", "exit"]:
                break

            decision = await decide_tool(user_input, tools)
            if "error" in decision:
                print("Gemini parsing error:", decision, "\n")
                continue

            tool = decision.get("tool")
            args = decision.get("args", {})

            print(f"Gemini decided: {decision}")

            # Call MCP tool
            try:
                result = await client.call_tool(tool, args)
                print("Result:", result, "\n")
            except Exception as e:
                print(f"MCP call failed: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())
