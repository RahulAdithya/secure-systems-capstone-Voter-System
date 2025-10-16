from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, users, ballots

app = FastAPI(title="Electronic Voting Platform (Base)")

# Open CORS for local dev (will harden later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ballots.router)
