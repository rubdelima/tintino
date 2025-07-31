from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.database import db
from api.utils.logger import get_logger

logger = get_logger(__name__)

security_bearer = HTTPBearer()

def verify_user(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)):
    """Verify user credentials."""
    
    token = credentials.credentials
    
    if not db.verify_user(token):
        logger.warning(f"Usuário não verificado: {token}")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return token