from fastapi import FastAPI, UploadFile, File, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import shutil
import json

# Import our custom modules
import database
import rag
import gemini_client

app = FastAPI(title="AI Career Copilot")

# Set up static files (CSS, etc.) and templates (HTML)
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    database.init_db()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renders the main page with chat history."""
    messages = database.get_all_messages()
    return templates.TemplateResponse(request=request, name="index.html", context={"messages": messages})

@app.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    """Handles PDF resume upload, extracts text, and stores in ChromaDB."""
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are supported."}
        
    # Save the file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Process it through our RAG pipeline
        num_chunks = rag.process_and_store_resume(temp_file_path)
        
        # Add a system message so the user knows it worked
        database.save_message("system", f"Resume '{file.filename}' uploaded successfully. Resume processed and stored in vector memory.")
        
        # Extract and save career memory profile
        full_text = rag.get_all_chunks()
        profile_json_str = gemini_client.extract_user_profile(full_text)
        database.save_user_profile(profile_json_str)
        
        return {"success": True, "message": "Resume processed and stored in vector memory."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/chat")
async def chat(request: Request):
    """Handles a chat message from the user."""
    form_data = await request.form()
    question = form_data.get("question", "").strip()
    
    if not question:
        return {"error": "Question cannot be empty."}
        
    # 1. Save user's message to DB
    database.save_message("user", question)
    
    # 2. Retrieve relevant chunks from ChromaDB
    # We get top 3 most relevant chunks
    relevant_chunks = rag.query_resume(question, n_results=3)
    
    # 3. Call Gemini with the question, chunks, and the high-level user profile
    user_profile_json = database.get_user_profile()
    ai_response = gemini_client.generate_career_advice(question, relevant_chunks, user_profile_json)
    
    # 4. Save AI's response to DB
    database.save_message("assistant", ai_response)
    
    return {
        "user_message": question, 
        "ai_response": ai_response,
        "context": relevant_chunks
    }

@app.get("/api/profile")
async def get_profile():
    """Returns the parsed career memory profile."""
    profile_str = database.get_user_profile()
    if profile_str:
        try:
            return json.loads(profile_str)
        except:
            return {}
    return {}

@app.post("/api/generate_interview")
async def generate_interview():
    """Generates 5 personalized technical interview questions based on the resume."""
    full_text = rag.get_all_chunks()
    if not full_text.strip():
        return {"error": "No resume context found. Please upload a resume first."}
        
    ai_response = gemini_client.generate_interview_questions(full_text)
    
    # Save the interaction to DB
    database.save_message("user", "Generate Interview Questions")
    database.save_message("assistant", ai_response)
    
    return {"ai_response": ai_response}

@app.post("/clear_history")
async def clear_chat_history():
    """Clears the chat history."""
    database.clear_history()
    return {"success": True}
