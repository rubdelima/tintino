from firebase_admin import auth
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.database import db
from api.utils.logger import get_logger
from api.constraints import config
import json
from api.database.firebase import get_credentials_file

logger = get_logger(__name__)

security_bearer = HTTPBearer()
DEFAULT_USER = config.get("APISettings", {}).get("test_user", "")

# Obter o project_id do firebase.json para validação
try:
    with open(get_credentials_file(), 'r') as f:
        firebase_config = json.load(f)
        EXPECTED_PROJECT_ID = firebase_config.get('project_id')
except Exception as e:
    logger.error(f"Erro ao carregar firebase.json: {e}")
    EXPECTED_PROJECT_ID = None
    raise HTTPException(status_code=401, detail="Firebase config not loaded")

def _verify_token_core(token: str) -> str:
    """
    Lógica central de verificação de token, reutilizada por outras funções.
    
    Args:
        token: Token JWT como string
        
    Returns:
        str: ID do usuário se o token for válido
        
    Raises:
        HTTPException: Se o token for inválido
    """
    if config.get("Database", {}).get("local", True):
        # Modo local
        if not db.verify_user(token):
            logger.warning(f"Usuário não verificado: {token}")
            raise HTTPException(status_code=401, detail="Unauthorized")
        return token
    else:
        # Modo Firebase
        if token == DEFAULT_USER:
            return token
            
        try:
            # Primeiro, tentar com verificação padrão
            decoded_token = auth.verify_id_token(token)
            
            # Verificar se o token pertence ao nosso projeto Firebase
            if EXPECTED_PROJECT_ID and decoded_token.get('aud') != EXPECTED_PROJECT_ID:
                logger.warning(f"Token de projeto Firebase incorreto. Esperado: {EXPECTED_PROJECT_ID}, Recebido: {decoded_token.get('aud')}")
                raise HTTPException(status_code=401, detail="Unauthorized - Invalid Firebase project")
            
            return decoded_token['uid']
        except auth.InvalidIdTokenError as e:
            # Se falhar por questões de tempo, tentar novamente sem verificação de tempo
            try:
                logger.info(f"Token com problema de tempo, tentando verificação permissiva: {e}")
                decoded_token = auth.verify_id_token(token, check_revoked=False, clock_skew_seconds=86400)  # 24 horas de tolerância
                
                # Verificar se o token pertence ao nosso projeto Firebase
                if EXPECTED_PROJECT_ID and decoded_token.get('aud') != EXPECTED_PROJECT_ID:
                    logger.warning(f"Token de projeto Firebase incorreto. Esperado: {EXPECTED_PROJECT_ID}, Recebido: {decoded_token.get('aud')}")
                    raise HTTPException(status_code=401, detail="Unauthorized - Invalid Firebase project")
                
                logger.info(f"Token aceito com verificação permissiva para UID: {decoded_token['uid']}")
                return decoded_token['uid']
            except Exception as inner_e:
                logger.warning(f"Token Firebase inválido mesmo com verificação permissiva: {inner_e}")
                raise HTTPException(status_code=401, detail="Unauthorized")
        except HTTPException:
            # Re-raise HTTPExceptions para manter o status code correto
            raise
        except Exception as e:
            logger.warning(f"Token Firebase inválido: {e}")
            raise HTTPException(status_code=401, detail="Unauthorized")

def verify_token_local(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> str:
    token = credentials.credentials
    return _verify_token_core(token)

def verify_token_firebase(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> str:
    token = credentials.credentials
    return _verify_token_core(token)

verify_token = verify_token_local if config.get("Database", {}).get("local", True) else verify_token_firebase

def verify_token_string(token: str) -> str:
    """
    Verifica um token passado como string (para uso em WebSockets).
    Reutiliza a mesma lógica das funções de autenticação HTTP.
    
    Args:
        token: Token JWT como string
        
    Returns:
        str: ID do usuário se o token for válido
        
    Raises:
        HTTPException: Se o token for inválido
    """
    return _verify_token_core(token)
