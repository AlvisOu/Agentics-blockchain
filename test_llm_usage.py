# test_llm_usage.py
from agentics import LLM, user_message, system_message
import os
from dotenv import load_dotenv

load_dotenv()

# Check if we can use Anthropic or need OpenAI
api_key = os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY')

if not api_key:
    print("❌ No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env")
    exit(1)

print("Testing IBM Agentics LLM...")

# Try to initialize
try:
    # Test with OpenAI model
    llm = LLM(model="gpt-4o-mini")
    print("✓ LLM initialized with gpt-4o-mini")
    
    # Test chat
    messages = [
        system_message("You are a helpful assistant."),
        user_message("Say 'Hello from IBM Agentics!' if you can read this.")
    ]
    
    response = llm.chat(messages=messages)
    print(f"✓ Response: {response}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nIBM Agentics appears to require OpenAI API key.")
    print("Add to .env: OPENAI_API_KEY=sk-...")