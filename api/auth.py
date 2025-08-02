from firebase_admin import auth
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.database import db
from api.utils.logger import get_logger
from api.constraints import config
import json

logger = get_logger(__name__)

security_bearer = HTTPBearer()
DEFAULT_USER = config.get("APISettings", {}).get("test_user", "")

# Obter o project_id do firebase.json para validação
try:
    with open('firebase.json', 'r') as f:
        firebase_config = json.load(f)
        EXPECTED_PROJECT_ID = firebase_config.get('project_id')
except Exception as e:
    logger.error(f"Erro ao carregar firebase.json: {e}")
    EXPECTED_PROJECT_ID = None

def verify_token_local(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> str:
    token = credentials.credentials
    if not db.verify_user(token) :
        logger.warning(f"Usuário não verificado: {token}")
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token

def verify_token_firebase(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> str:
    token = credentials.credentials
    
    if token == DEFAULT_USER:
        return token
        
    try:
        decoded_token = auth.verify_id_token(token)
        
        # Verificar se o token pertence ao nosso projeto Firebase
        if EXPECTED_PROJECT_ID and decoded_token.get('aud') != EXPECTED_PROJECT_ID:
            logger.warning(f"Token de projeto Firebase incorreto. Esperado: {EXPECTED_PROJECT_ID}, Recebido: {decoded_token.get('aud')}")
            raise HTTPException(status_code=401, detail="Unauthorized - Invalid Firebase project")
        
        return decoded_token['uid']
    except HTTPException:
        # Re-raise HTTPExceptions para manter o status code correto
        raise
    except Exception as e:
        logger.warning(f"Token Firebase inválido: {e}")
        raise HTTPException(status_code=401, detail="Unauthorized")

verify_token = verify_token_local if config.get("Database", {}).get("local", True) else verify_token_firebase
