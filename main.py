from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "✅ Brainwash Labs Backend is running!"}
