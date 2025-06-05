import nest_asyncio
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ci_agent.routers import agentconfig, auth, chat, search
from ci_agent.main_deps import gen_deps
load_dotenv("./.env")
nest_asyncio.apply()

app = FastAPI(title="Competitive Intelligence Agent API", version="0.1.0")

origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(search.router, dependencies=[Depends(gen_deps)])
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
    uvicorn.run("ci_agent.main:app", host="0.0.0.0", port=8080, reload=True)