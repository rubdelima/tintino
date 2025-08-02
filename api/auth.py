from firebase_admin import auth
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.database import db
from api.utils.logger import get_logger
from api.constraints import config

logger = get_logger(__name__)

security_bearer = HTTPBearer()
DEFAULT_USER = config.get("APISettings", {}).get("test_user", "f4b7b9e2-b26a-480a-ac43-0e085482390f")

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
        return decoded_token['uid']
    except Exception as e:
        logger.warning(f"Token Firebase inválido: {e}")
        raise HTTPException(status_code=401, detail="Unauthorized")

verify_token = verify_token_local if config.get("Database", {}).get("local", True) else verify_token_firebase
