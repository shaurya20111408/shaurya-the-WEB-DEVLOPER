from fastapi import FastAPI

app = FastAPI(title="Private Search")


@app.get("/hello")
def hello():
    return {"message": "Private search engine chal raha hai!"}