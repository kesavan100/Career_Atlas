import os
import PyPDF2
import chromadb
from sentence_transformers import SentenceTransformer

# ─────────────────────────────────────────────────────────────────────────────
# AZURE FIX: Lazy model loading
# Previously the model was loaded at import time, which made FastAPI take
# 3-5 minutes to start — causing Azure's 230s startup timeout to trigger.
# Now the model only loads when the first actual request comes in.
# FastAPI starts instantly, passes the Azure health check, then loads the model.
# ─────────────────────────────────────────────────────────────────────────────
_embedding_model = None  # model starts as None

def get_embedding_model():
    """Returns the embedding model, loading it on first use (lazy loading)."""
    global _embedding_model
    if _embedding_model is None:
        print("Loading embedding model for the first time...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Embedding model loaded successfully!")
    return _embedding_model


# ─────────────────────────────────────────────────────────────────────────────
# PATH DETECTION: Azure vs Local
# On Azure App Service, /home is the only folder that persists between restarts.
# WEBSITE_INSTANCE_ID is an environment variable Azure sets automatically.
# ─────────────────────────────────────────────────────────────────────────────
if os.environ.get("WEBSITE_INSTANCE_ID"):
    CHROMA_PATH = "/home/chroma_db"       # Azure persistent storage
    MODEL_CACHE = "/home/model_cache"     # Cache downloaded model on Azure
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = MODEL_CACHE
    os.makedirs(MODEL_CACHE, exist_ok=True)
else:
    CHROMA_PATH = "./chroma_db"           # Local development

os.makedirs(CHROMA_PATH, exist_ok=True)
print(f"ChromaDB path: {CHROMA_PATH}")

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(
    path=CHROMA_PATH,
    settings=chromadb.Settings(anonymized_telemetry=False)
)
collection_name = "resume_chunks"


# VIVA COMMENT: ChromaDB needs a wrapper class to use our sentence-transformers model.
# We call get_embedding_model() inside the function so the model loads lazily.
class MyEmbeddingFunction(chromadb.EmbeddingFunction):
    def __call__(self, input: list[str]) -> list[list[float]]:
        model = get_embedding_model()  # loads model if not already loaded
        embeddings = model.encode(input)
        return embeddings.tolist()


collection = chroma_client.get_or_create_collection(
    name=collection_name,
    embedding_function=MyEmbeddingFunction()
)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a given PDF file."""
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text


def split_text_into_chunks(text: str, chunk_size: int = 100, overlap: int = 20) -> list[str]:
    """Splits a long text into smaller chunks with some overlap."""
    # VIVA COMMENT (Chunking): We split the resume into smaller chunks so that we don't exceed the AI's
    # token limit, and to ensure we retrieve only the most relevant sections instead of the whole document.
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
    return chunks


def process_and_store_resume(pdf_path: str):
    """Extracts text, splits it, and stores it in ChromaDB."""
    full_text = extract_text_from_pdf(pdf_path)
    if not full_text.strip():
        raise ValueError("Could not extract any text from the PDF.")

    chunks = split_text_into_chunks(full_text)

    try:
        chroma_client.delete_collection(collection_name)
    except:
        pass

    global collection
    collection = chroma_client.create_collection(
        name=collection_name,
        embedding_function=MyEmbeddingFunction()
    )

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": "resume"} for _ in chunks]

    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )

    return len(chunks)


def query_resume(question: str, n_results: int = 3) -> list[dict]:
    """Queries ChromaDB to find the most relevant resume chunks for a question."""
    # VIVA COMMENT (Retrieval): We convert the user's question into an embedding,
    # then ChromaDB finds the top 3 resume chunks with the closest meaning.
    try:
        results = collection.query(
            query_texts=[question],
            n_results=n_results
        )
        if results and results['documents'] and len(results['documents']) > 0:
            retrieved = []
            for i in range(len(results['documents'][0])):
                retrieved.append({
                    "text": results['documents'][0][i],
                    "id": results['ids'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results and results['distances'] else None
                })
            return retrieved
        return []
    except Exception as e:
        print(f"Error querying resume: {e}")
        return []


def get_all_chunks() -> str:
    """Retrieves all stored resume chunks to construct the full resume text."""
    try:
        results = collection.get()
        if results and results['documents']:
            return "\n\n".join(results['documents'])
        return ""
    except Exception as e:
        print(f"Error retrieving all chunks: {e}")
        return ""
