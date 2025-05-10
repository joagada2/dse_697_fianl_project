import os
import logging
from typing import List, Dict
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import redis
import json
import torch
from transformers import DPRQuestionEncoder, DPRQuestionEncoderTokenizer
from langchain_openai import ChatOpenAI
from pinecone import Pinecone
from langchain.schema import SystemMessage, HumanMessage

########################################
# Load Env / Config
########################################
load_dotenv()
import os
from redis import Redis

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_client = Redis.from_url(redis_url)

# Unified Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")  # Default to 'redis' for Docker
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

########################################
# Initialize Redis with robust connection handling
########################################
def get_redis_client():
    try:
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            decode_responses=True
        )
        client.ping()  # Test connection
        return client
    except redis.ConnectionError as e:
        logging.error(f"Redis connection error: {e}")
        return None

redis_client = get_redis_client()

#import torch
from transformers import DPRQuestionEncoder, DPRQuestionEncoderTokenizer

# Use GPT-4 via ChatOpenAI for final generation
from langchain_openai import ChatOpenAI
from pinecone import Pinecone
from langchain.schema import SystemMessage, HumanMessage

########################################
# Load Env / Config
########################################
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# DPR + GPT settings
QUESTION_ENCODER_MODEL = "facebook/dpr-question_encoder-single-nq-base"
# You must ensure your Pinecone index is dimension=768 with dotproduct
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_API_ENV = os.getenv("PINECONE_API_ENV", "us-east-1")
INDEX_NAME = "ut-rag-app"  # The same index used in your ingestion pipeline (768D)
TOP_K = 50  # how many results to fetch from Pinecone

# LLM (GPT-4)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# llm = ChatOpenAI(model_name="gpt-4o", openai_api_key=OPENAI_API_KEY, temperature=0.0)
llm = ChatOpenAI(model="gpt-4", api_key=OPENAI_API_KEY, temperature=0.0)

########################################
# Init Pinecone
########################################
pc = Pinecone(api_key=PINECONE_API_KEY)
pinecone_index = pc.Index(INDEX_NAME)

########################################
# DPR Question Encoder
########################################
q_tokenizer = DPRQuestionEncoderTokenizer.from_pretrained(QUESTION_ENCODER_MODEL)
q_encoder = DPRQuestionEncoder.from_pretrained(QUESTION_ENCODER_MODEL)
q_encoder.eval()

def embed_query_dpr(query: str) -> list:
    """
    Encodes a user query using DPR's question encoder -> 768-dim vector.
    """
    inputs = q_tokenizer(query, return_tensors="pt", truncation=True, max_length=512, padding=True)
    with torch.no_grad():
        emb = q_encoder(**inputs).pooler_output  # shape [1, 768]
    return emb[0].tolist()

########################################
# Redis for conversation memory
########################################
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

########################################
# FastAPI Setup
########################################
app = FastAPI(title="RAG Chat API with DPR + Redis")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    session_id: str = None

class ResetRequest(BaseModel):
    session_id: str

########################################
# Prompt + Retrieval
########################################
def build_prompt(query: str, context: str, history: str) -> List:
    return [
        SystemMessage(
            content=(
                "You are ChatGPT, a large language model trained by OpenAI.\n"
                "Answer conversationally, helpfully, and in elaborately.\n"
                "If relevant, you must mention the source in the answer using the URL below.\n"
                "If you cite text from the snippet, mention the 'Source URL:' from that snippet.\n"
                "If the answer isn’t in the context below, reply 'provide answer with your own knowledge but indicate "
                "the answer is from you and not from the context provided.'\n"
                "Format answers in Markdown.\n"
            )
        ),
        HumanMessage(
            content=f"""
Conversation History:
{history}

Context:
{context}

Question: {query}
"""
        ),
    ]


def retrieve_context(query: str, top_k: int = TOP_K) -> str:
    """
    Use DPR question encoder to embed the user query, then Pinecone dot-product search for top_k results.
    """
    # 1) embed query with DPR
    query_vector = embed_query_dpr(query)

    # 2) search Pinecone
    results = pinecone_index.query(vector=query_vector, top_k=top_k, include_metadata=True)

    # 3) format retrieved chunks
    context_pieces = []
    for match in results.get("matches", []):
        md = match.get("metadata", {})
        text = md.get("text", "")
        url = md.get("url", "N/A")
        snippet = f"{text}\nSource URL: {url}"
        context_pieces.append(snippet)

    return "\n\n".join(context_pieces)

def generate_answer(query: str, session_id: str) -> str:
    # load chat history from redis
    history_str = ""
    saved = redis_client.get(session_id)
    if saved:
        history_list = json.loads(saved)
        history_str = "\n".join(history_list)
    else:
        history_list = []

    # retrieve context from Pinecone
    context = retrieve_context(query, top_k=TOP_K)

    # build prompt
    messages = build_prompt(query, context, history_str)
    logging.info("Invoking GPT-4 with DPR-based retrieval...")

    # call GPT-4 with the final prompt
    response = llm.invoke(messages)

    # update conversation memory
    history_list.extend([f"User: {query}", f"Assistant: {response.content}"])
    redis_client.set(session_id, json.dumps(history_list))

    return response.content

########################################
# Endpoints
########################################
@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        session_id = req.session_id or str(uuid4())
        answer = generate_answer(req.query, session_id)
        return {"answer": answer, "session_id": session_id}
    except Exception as e:
        logging.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset-session")
async def reset_session(req: ResetRequest):
    try:
        redis_client.delete(req.session_id)
        return {"message": f"Session {req.session_id} has been reset."}
    except Exception as e:
        logging.error(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
