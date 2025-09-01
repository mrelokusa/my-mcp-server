from fastapi import FastAPI
import os, uvicorn

app = FastAPI()

@app.get("/")
def root():
    return {"message": "MCP server is alive on Render!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
