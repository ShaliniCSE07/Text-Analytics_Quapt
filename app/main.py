from fastapi import FastAPI

app = FastAPI(title="Text Analytics Pipeline")

@app.get("/health")
def health_check():
    return {"status": "ok"}
