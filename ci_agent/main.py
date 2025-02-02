import nest_asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from ci_agent.routers import agentconfig, chat, search

load_dotenv()
nest_asyncio.apply()

app = FastAPI(title="Competitive Intelligence Agent API", version="0.1.0")

# Routers
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(agentconfig.router)

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
    uvicorn.run("ci_agent.main:app", host="127.0.0.1", port=8000, reload=True)