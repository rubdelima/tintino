import api.utils.logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import json

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

import firebase_admin
from firebase_admin import credentials

try:
    firebase_config_str = os.getenv('FIREBASE_CREDENTIALS_JSON')
    if firebase_config_str:
        cred = credentials.Certificate(json.loads(firebase_config_str))
    else:
        cred = credentials.Certificate(get_credentials_file())

    firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin SDK inicializado com sucesso.")
except Exception as e:
    logger.error(f"Erro ao inicializar Firebase Admin SDK: {e}")

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
