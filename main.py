from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Streaming Avatar FastAPI Backend")

# CORS middleware to allow requests from Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "https://your-frontend.vercel.app"  # Replace with your actual deployed frontend URL
    ],  # Next.js dev server and production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
HEYGEN_BASE_URL = os.getenv("HEYGEN_BASE_URL", "https://api.heygen.com")

class KnowledgeBaseRequest(BaseModel):
    name: str
    opening: str
    prompt: str

class StartSessionRequest(BaseModel):
    name: str
    opening: str
    prompt: str

@app.post("/get-access-token")
async def get_access_token():
    if not HEYGEN_API_KEY:
        raise HTTPException(status_code=500, detail="API key is missing from environment")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{HEYGEN_BASE_URL}/v1/streaming.create_token",
                headers={"x-api-key": HEYGEN_API_KEY}
            )
            response.raise_for_status()
            data = response.json()
            return {"token": data["data"]["token"]}
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Failed to retrieve access token")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-knowledge-base")
async def create_knowledge_base(request: KnowledgeBaseRequest):
    if not HEYGEN_API_KEY:
        raise HTTPException(status_code=500, detail="API key is missing from environment")

    async with httpx.AsyncClient() as client:
        try:
            # Create the knowledge base
            response = await client.post(
                f"{HEYGEN_BASE_URL}/v1/streaming/knowledge_base/create",
                headers={
                    "accept": "application/json",
                    "content-type": "application/json",
                    "x-api-key": HEYGEN_API_KEY
                },
                json={
                    "name": request.name,
                    "opening": request.opening,
                    "prompt": request.prompt
                }
            )
            response.raise_for_status()
            data = response.json()
            kb_id = data.get("data", {}).get("knowledge_base_id")

            # If ID is not in response, fetch the list and match
            if not kb_id:
                list_response = await client.get(
                    f"{HEYGEN_BASE_URL}/v1/streaming/knowledge_base/list",
                    headers={
                        "accept": "application/json",
                        "x-api-key": HEYGEN_API_KEY
                    }
                )
                list_response.raise_for_status()
                list_data = list_response.json()
                kb_list = list_data.get("data", {}).get("list", [])

                # Match by name, opening, and prompt
                for kb in kb_list:
                    if (kb.get("name") == request.name and
                        kb.get("opening") == request.opening and
                        kb.get("prompt") == request.prompt):
                        kb_id = kb.get("id")
                        break

            return {"knowledge_base_id": kb_id}
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Failed to create or retrieve knowledge base")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/start-session")
async def start_session(request: StartSessionRequest):
    if not HEYGEN_API_KEY:
        raise HTTPException(status_code=500, detail="API key is missing from environment")

    async with httpx.AsyncClient() as client:
        try:
            # Create the knowledge base
            kb_response = await client.post(
                f"{HEYGEN_BASE_URL}/v1/streaming/knowledge_base/create",
                headers={
                    "accept": "application/json",
                    "content-type": "application/json",
                    "x-api-key": HEYGEN_API_KEY
                },
                json={
                    "name": request.name,
                    "opening": request.opening,
                    "prompt": request.prompt
                }
            )
            kb_response.raise_for_status()
            kb_data = kb_response.json()
            kb_id = kb_data.get("data", {}).get("knowledge_base_id")

            # If ID is not in response, fetch the list and match
            if not kb_id:
                list_response = await client.get(
                    f"{HEYGEN_BASE_URL}/v1/streaming/knowledge_base/list",
                    headers={
                        "accept": "application/json",
                        "x-api-key": HEYGEN_API_KEY
                    }
                )
                list_response.raise_for_status()
                list_data = list_response.json()
                kb_list = list_data.get("data", {}).get("list", [])

                # Match by name, opening, and prompt
                for kb in kb_list:
                    if (kb.get("name") == request.name and
                        kb.get("opening") == request.opening and
                        kb.get("prompt") == request.prompt):
                        kb_id = kb.get("id")
                        break

            # Get access token
            token_response = await client.post(
                f"{HEYGEN_BASE_URL}/v1/streaming.create_token",
                headers={"x-api-key": HEYGEN_API_KEY}
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            token = token_data["data"]["token"]

            return {
                "knowledge_base_id": kb_id,
                "access_token": token
            }
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Failed to create session")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Streaming Avatar FastAPI Backend"}