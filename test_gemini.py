import os
from dotenv import load_dotenv
from google import genai

# 1. Load the .env file explicitly
# This is the "missing link" that connects your .env file to os.getenv
load_dotenv() 

# 2. Retrieve the key
gemini_key = os.getenv("GEMINI_API_KEY")

if not gemini_key:
    print("❌ ERROR: GEMINI_API_KEY not found in environment!")
    print("Ensure your .env file is in the same folder as this script.")
    exit(1)

# 3. Initialize the New Client (2026 Recommended Method)
# The new SDK uses a Client object rather than direct model configuration
client = genai.Client(api_key=gemini_key)

print("Testing Gemini API...")

try:
    # 4. Generate content using the new client structure
    # Note: 'gemini-pro' is now often aliased to 'gemini-1.5-flash' or 'gemini-2.0-flash'
    response = client.models.generate_content(
        model="gemini-2.5-flash",  # Changed from 2.0 to 2.5
        contents="Say hello!"
)

    print(f"✅ Gemini API Working!")
    print(f"Response: {response.text}")

except Exception as e:
    print(f"❌ API Call Failed: {e}")