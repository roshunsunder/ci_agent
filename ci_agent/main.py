from fastapi import FastAPI, Request, HTTPException

app = FastAPI(title="Competitive Intelligence Agent API", version="0.1.0")

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