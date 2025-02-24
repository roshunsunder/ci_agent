import nest_asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ci_agent.routers import agentconfig, auth, chat, search

# REMOVE
import requests
SEARXNG_URL = "http://searxng:8080/search"
def search_query(query):
    params = {"q": query, "format": "json"}
    response = requests.get(SEARXNG_URL, params=params)
    return response

print(search_query("FastAPI Docker integration"))
# /REMOVE

load_dotenv("./.env")
nest_asyncio.apply()

app = FastAPI(title="Competitive Intelligence Agent API", version="0.1.0")

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(agentconfig.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "Hello world"}

@app.get("/health")
async def health():
    return {
        "application": "Competitive Intelligence Agent API", 
        "message": "Running Successfully!"
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Agent API")
    uvicorn.run("ci_agent.main:app", host="0.0.0.0", port=8000, reload=True)