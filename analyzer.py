# analyzer.py
import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

# Local development ke liye .env load karega, Render par system environment variables use honge
load_dotenv()

def get_client():
    """Groq client ko safe tareeqe se initialize karta hai."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

def clean_json_response(raw_text: str) -> str:
    """
    LLM ke response se sirf JSON nikalne ke liye robust logic.
    Agar LLM ```json ... ``` bhejta hai ya extra text, ye sirf { ... } pakray ga.
    """
    # Regex use karke curly braces ke darmiyan wala content nikalna
    match = re.search(r'(\{.*\}|\[.*\])', raw_text, re.DOTALL)
    if match:
        return match.group(0)
    return raw_text

def analyze_feedback(feedback_text: str) -> dict:
    client = get_client()
    
    if not client:
        return {
            "success": False, 
            "error": "GROQ_API_KEY missing! Please set it in Render Dashboard -> Environment Variables."
        }
    
    system_prompt = """You are a professional business analyst. 
    Analyze the feedback and return ONLY a valid JSON object. 
    No markdown blocks, no intro, no outro."""
    
    user_prompt = f"""Analyze this feedback: "{feedback_text}"
    Return JSON with: sentiment, sentiment_score (-1 to 1), emotion, confidence, summary, 
    key_topics (list), positive_aspects (list), negative_aspects (list), 
    actionable_recommendation, priority (High/Medium/Low)."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1, # Consistency ke liye low temperature
            max_tokens=600,
        )
        
        raw_content = response.choices[0].message.content.strip()
        json_str = clean_json_response(raw_content)
        
        result = json.loads(json_str)
        return {"success": True, "data": result}
        
    except Exception as e:
        return {"success": False, "error": f"Analysis failed: {str(e)}"}

def analyze_batch(feedbacks_text: str) -> list:
    # Newlines par split karke empty lines ko remove karna
    lines = [line.strip() for line in feedbacks_text.split('\n') if len(line.strip()) > 5]
    
    results = []
    for i, line in enumerate(lines):
        analysis = analyze_feedback(line)
        analysis["original_text"] = line
        analysis["index"] = i + 1
        results.append(analysis)
    
    return results