# AI Career Copilot

This is a simple student project that lets you upload your resume (PDF) and chat with an AI Career Copilot. It remembers your resume using Retrieval-Augmented Generation (RAG) and gives you personalized career advice based on the skills and experiences you have.
<img width="1918" height="1007" alt="CareerAtlas (Screenshot 1)" src="https://github.com/user-attachments/assets/a88fd5fa-c56d-4dd5-9dea-24c30df4c807" />

<img width="1918" height="1012" alt="CareerAtlas (Screenshot 2)" src="https://github.com/user-attachments/assets/d214ee62-1d59-43dd-a527-5a2f5b911955" />

<img width="1918" height="1013" alt="CareerAtlas (Screenshot 3)" src="https://github.com/user-attachments/assets/6623695a-f5f7-4d95-b6cd-1adc998cea3a" />

## Features
- **Upload Resume**: Upload your resume in PDF format. Text is extracted and stored securely in a local vector database.
- **Chat with AI**: Ask the AI anything about your career path, what skills to learn next, or how you can improve your resume.
- **RAG Powered**: The AI will search your uploaded resume for context and provide personalized answers using Google's Gemini.

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: HTML, CSS (with Tailwind CSS via CDN)
- **AI / LLM**: Google Gemini API
- **Embeddings**: Sentence Transformers (runs locally)
- **Database**: ChromaDB (vector storage for resume), SQLite (chat history)

## How to run it locally

1. **Clone or download the project**

2. **Set up a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up API Key**
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Open `.env` and paste your Google Gemini API key.

5. **Run the server**
   ```bash
   uvicorn main:app --reload
   ```

6. **Open in Browser**
   Go to `http://127.0.0.1:8000` to start chatting!
