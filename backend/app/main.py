from fastapi import FastAPI

app = FastAPI(
    title="Collections Intelligence Agent",
    description="Pre-delinquency collections AI system",
    version="1.0"
)

@app.get("/")
def health_check():
    return {"status": "Collections Intelligence Agent Running"}



##Hi HI