import os
from groq import Groq
from dotenv import load_dotenv  

# Load the environmental variables from your local .env file
load_dotenv()

# Pull the API key from your local system environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize the Groq SDK client safely
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def analyze_llm_attribution(text: str) -> float:
    """
    Signal 1: LLM-Based Attribution Analysis
    
    Evaluates tone consistency, predictability, and structural repetition 
    using llama-3.3-70b-versatile.
    
    Returns:
        float: A score between 0.0 (likely human) and 1.0 (likely AI).
    """
    if not groq_client:
        raise ValueError("Critical Error: 'GROQ_API_KEY' environment variable is missing.")

    if not text or not text.strip():
        return 0.0  # Safe guard for empty strings

    # Instructing the model strictly to match the system data requirements
    system_prompt = (
        "You are an expert forensic linguist analyzing writing patterns.\n"
        "Evaluate the provided text for tone consistency, uniformity, and phrasing predictability.\n"
        "Respond with a single raw decimal score between 0.00 and 1.00 indicating the probability "
        "that the text is AI-generated (0.00 = human, 1.00 = AI).\n"
        "Do NOT include explanations, words, formatting, or punctuation. Output only the number."
    )

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.0,  # Forces maximum predictability and determinism
            max_tokens=10     # Limits response length so it only gives the score
        )
        
        raw_output = completion.choices[0].message.content.strip()
        score = float(raw_output)
        
        # Clip the score between 0.0 and 1.0 to handle anomalies safely
        return max(0.0, min(1.0, score))
        
    except Exception as e:
        print(f"Signal 1 execution anomaly: {str(e)}")
        return 0.50  # Return baseline uncertainty fallback on network failure


# =====================================================================
# INDEPENDENT TEST SANDBOX
# =====================================================================
if __name__ == "__main__":
    # This block ONLY runs when you execute `python pipeline.py` directly.
    # It allows you to test your AI function independently of Flask!
    print("--- Testing Signal 1 Function Independently ---")
    
    test_human = "ok so i finally tried that new ramen place downtown and honestly? underwhelming."
    test_ai = "Artificial intelligence represents a transformative paradigm shift in modern human society."
    
    print(f"Testing Human Text. Expected close to 0.0. Result -> {analyze_llm_attribution(test_human)}")
    print(f"Testing AI Text. Expected close to 1.0.    Result -> {analyze_llm_attribution(test_ai)}")