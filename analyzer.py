import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from a .env file for local development.
# On production platforms like Render, system environment variables will be used.
load_dotenv()

def get_client():
    """
    Securely initializes the Groq client.
    Returns:
        Groq: Initialized client if the API key is present, otherwise None.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

def clean_json_response(raw_text: str) -> str:
    """
    Extracts the JSON content from the LLM's raw response.
    Uses regex to isolate content within curly or square brackets to ensure 
    robustness even if the LLM includes Markdown blocks or conversational text.
    """
    # Use regular expression to find the JSON structure within the response
    match = re.search(r'(\{.*\}|\[.*\])', raw_text, re.DOTALL)
    if match:
        return match.group(0)
    return raw_text

def analyze_feedback(feedback_text: str) -> dict:
    """
    Analyzes individual feedback using the Llama model via the Groq API.
    Processes the sentiment, emotion, and provides actionable recommendations.
    """
    client = get_client()
    
    # Validation to ensure the API key is configured
    if not client:
        return {
            "success": False, 
            "error": "GROQ_API_KEY missing! Please set it in Render Dashboard -> Environment Variables."
        }
    
    # System prompt to define the AI's persona and strict output constraints
    system_prompt = """You are a professional business analyst. 
    Analyze the feedback and return ONLY a valid JSON object. 
    No markdown blocks, no intro, no outro."""
    
    # User prompt specifying the required JSON schema
    user_prompt = f"""Analyze this feedback: "{feedback_text}"
    Return JSON with: sentiment, sentiment_score (-1 to 1), emotion, confidence, summary, 
    key_topics (list), positive_aspects (list), negative_aspects (list), 
    actionable_recommendation, priority (High/Medium/Low)."""

    try:
        # API call to the Groq inference engine
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1, # Low temperature for consistent and deterministic output
            max_tokens=600,
        )
        
        # Extract and clean the content from the response
        raw_content = response.choices[0].message.content.strip()
        json_str = clean_json_response(raw_content)
        
        # Parse the string into a dictionary
        result = json.loads(json_str)
        return {"success": True, "data": result}
        
    except Exception as e:
        # Graceful error handling for API or parsing failures
        return {"success": False, "error": f"Analysis failed: {str(e)}"}

def analyze_batch(feedbacks_text: str) -> list:
    """
    Processes multiple lines of feedback.
    Splits the input string into individual feedback items and analyzes each sequentially.
    """
    # Split input text into lines and filter out empty or very short strings
    lines = [line.strip() for line in feedbacks_text.split('\n') if len(line.strip()) > 5]
    
    results = []
    for i, line in enumerate(lines):
        # Perform analysis on each valid line
        analysis = analyze_feedback(line)
        analysis["original_text"] = line
        analysis["index"] = i + 1
        results.append(analysis)
    
    return results