import os
from google import genai
from dotenv import load_dotenv

# Load environment variables (like API key)
load_dotenv(override=True)

# Configure the Gemini API client
api_key = os.getenv("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)

def generate_career_advice(question: str, resume_chunks: list[dict], user_profile_json: str = None) -> str:
    """
    Combines the user's question and relevant resume chunks, 
    then sends it to Gemini for an answer.
    """
    if not api_key:
        return "Error: GEMINI_API_KEY is not set in the .env file."
        
    # Prepare the context from the chunks
    context_text = "\n\n---\n\n".join([chunk["text"] for chunk in resume_chunks])
    
    if not context_text:
        context_text = "No resume context found. The user might not have uploaded a resume yet."
        
    # Parse user profile to get the name
    user_name = "the user"
    if user_profile_json:
        import json
        try:
            profile_data = json.loads(user_profile_json)
            if profile_data.get("name"):
                user_name = profile_data.get("name")
        except:
            pass
            
    # Construct the prompt
    prompt = f"""
    You are an AI Career Copilot speaking to {user_name}. Your job is to give helpful, encouraging, and actionable career advice.
    
    Below is some context retrieved from {user_name}'s resume:
    {context_text}
    
    # VIVA COMMENT (Prompt Augmentation): We augment the user's prompt with strict instructions 
    # to ground the AI's response in the retrieved context, reducing hallucinations.
    INSTRUCTIONS:
    1. Only use information found in the retrieved resume context above to answer the user's question about their experience or skills.
    2. If the user asks about something not present in the resume context, clearly say so before offering general advice.
    3. Do NOT hallucinate or invent fake experience, skills, or jobs for the user.
    4. Keep your answer concise, easy to read, and friendly.
    
    User's Question: {question}
    """
    
    try:
        # Using the gemini-1.5-flash model as it's fast and suitable for text
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Sorry, there was an error communicating with the AI: {str(e)}"

def extract_user_profile(resume_text: str) -> str:
    """Extracts skills, technologies, domains, and a suggested career path from the resume as JSON."""
    if not client or not resume_text:
        return "{}"
        
    prompt = f"""
    Analyze the following resume text and extract the key career profile information.
    Return ONLY a raw JSON object with the following keys, and nothing else (no markdown blocks, no extra text):
    {{
        "name": "User's Full Name (or Unknown if not found)",
        "skills": ["skill1", "skill2"],
        "technologies": ["tech1", "tech2"],
        "domains": ["domain1", "domain2"],
        "suggested_path": "A concise 3-4 word suggested career path (e.g., AI Backend Engineer)"
    }}
    
    Resume Text:
    {resume_text}
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.replace("```json", "").replace("```", "").strip()
    except Exception as e:
        print(f"Extraction error: {e}")
        return "{}"

def generate_interview_questions(resume_text: str) -> str:
    """Generates 5 personalized technical interview questions based on the resume."""
    if not client or not resume_text:
        return "Please upload a resume first."
        
    prompt = f"""
    Based on the following resume text, generate exactly 5 personalized technical interview questions.
    The questions should focus on the specific projects, technologies, APIs, or architectural decisions mentioned in the resume.
    Ask about challenges faced, model choices, or deployment decisions where relevant.
    
    Format the output as a clean markdown list.
    
    Resume Text:
    {resume_text}
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error generating questions: {e}"
