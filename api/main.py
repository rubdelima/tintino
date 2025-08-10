import api.utils.logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials

from api.routes import router as api_router

app = FastAPI(
    title="Louie API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="")

@app.on_event("startup")
def startup_event():
    """Initialize Firebase Admin SDK on startup."""
    if not firebase_admin._apps:  # prevents re-initialization on reload
        cred = credentials.Certificate(get_credentials_file())
        project_id = cred.project_id
        storage_bucket_url = f"{project_id}.firebasestorage.app"
        firebase_admin.initialize_app(cred, {
            'storageBucket': storage_bucket_url
        })

@app.get(
    "/", 
    status_code=200,
    summary="Endpoint raiz",
    description="Endpoint de boas-vindas que confirma que a API está funcionando.",
    tags=["Sistema"]
)
async def root():
    return {
        "message": "Welcome to the Louie API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "redoc": "/api/redoc"
    }
