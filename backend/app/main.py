from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers.chat import router as chat_router
from app.routers.profile import router as profile_router


load_dotenv()

app = FastAPI(title="Health AI Agent API", version="1.0.0")

# Allow local frontend development (Vite default: http://localhost:5173, also 5174).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router, prefix="/api")
app.include_router(profile_router, prefix="/api")


@app.get("/")
def health_check() -> dict:
    return {"status": "ok", "message": "Health AI Agent backend is running"}
