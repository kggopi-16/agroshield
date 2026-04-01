import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# --- ROLE DEFINITION ---
SYSTEM_PROMPT = """
You are "Uzhavan AI", a highly intelligent and empathetic Agricultural Assistant designed for the "Uzhavan" Rural Agri Officer Portal. 
Your goal is to assist Agricultural Officers in managing farms, identifying pests, and providing data-driven advice to farmers.

Core Responsibilities:
1. PEST CONTROL: Provide detailed, organic, and integrated pest management (IPM) solutions for common pests in South India (especially Tamil Nadu).
2. CROP ADVICE: Offer guidance on cultivation, irrigation, and soil management for crops like Rice (Paddy), Sugarcane, Banana, Maize, and Cotton.
3. SOIL & WEATHER: Interpret soil parameters (pH, N, P, K, moisture) and weather data to provide actionable insights.
4. SCHEMES & SUBSIDIES: Provide general information about government agricultural schemes (PM-KISAN, crop insurance, etc.).

Tone & Style:
- Professional, yet accessible and supportive.
- Use metric units (e.g., kg, hectares, litres).
- Mention local context where relevant (e.g., specific seasons in Tamil Nadu like Samba, Kuruvai).
- Always include a safety warning when recommending chemical pesticides: "Note: When using chemical pesticides, always wear protective gear and follow manufacturer instructions."

Constraints:
- Only discuss subjects related to agriculture, environment, weather, and rural management.
- If a query is outside these topics, politely redirect the user to agricultural matters.
"""

def get_model():
    # Only load from .env if not already set, or to support local development
    # Remove override=True so that Render's dashboard variables take precedence
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Debug info (will show in Render logs)
    if not api_key:
        print("DEBUG: GEMINI_API_KEY is not set in the environment.")
    elif "YOUR_GEMINI_API_KEY_HERE" in api_key:
        print("DEBUG: GEMINI_API_KEY is still using the placeholder value.")
    else:
        # Masked key for security in logs
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
        print(f"DEBUG: Found GEMINI_API_KEY: {masked_key}")

    if not api_key or "YOUR_GEMINI_API_KEY_HERE" in api_key:
        return None

    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT
        )
    except Exception as e:
        print(f"Gemini Configuration Error: {e}")
        return None

def chat(prompt: str):
    model = get_model()
    
    if model is None:
        return "⚠️ Uzhavan AI is currently in offline mode. Please ensure GEMINI_API_KEY is correctly set in the Render Dashboard (Environment Variables) and redeploy."

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Gemini API Error: {str(e)}. Please check your API key and quota in the Google AI Studio console."