from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List
import traceback

from api.schemas.messages import Chat, MiniChat, SubmitImageMessage, SubmitImageHandler
from api.services.chat import new_chat, continue_chat
from api.utils.logger import get_logger
from api.services.messages import submit_image, generate_feedback_audio
from api.database import db
from api.auth import verify_token

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/chats",
    tags=["Chats"],
    responses={
        401: {"description": "Token de autenticação inválido"},
        500: {"description": "Erro interno do servidor"}
    }
)

@router.post(
    "/", 
    response_model=Chat, 
    status_code=201,
    summary="Criar novo chat",
    description="""
    Inicia uma nova história interativa baseada em áudio.
    
    - Recebe um arquivo de áudio com a instrução inicial
    - Transcreve o áudio e gera a primeira parte da história
    - Cria elementos visuais para desenho
    - Retorna o chat completo com primeira mensagem
    
    O áudio deve conter uma instrução clara sobre que tipo de história
    a criança gostaria de ouvir (ex: "uma história sobre dinossauros").
    """,
    responses={
        201: {"description": "Chat criado com sucesso"},
        400: {"description": "Arquivo de áudio inválido"},
    }
)
async def create_chat(
    voice_audio: UploadFile, 
    user_id: str = Depends(verify_token)
):
    try:
        chat = await new_chat(user_id, voice_audio) #type:ignore
        logger.info(f"Chat de Título: {chat.title} - ID: {chat.chat_id}")
        return chat
    except HTTPException as http_exc:
        logger.error(f"Erro ao criar chat: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Erro ao criar chat: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get(
    "/", 
    response_model=List[MiniChat], 
    status_code=200,
    summary="Listar chats do usuário",
    description="""
    Retorna todos os chats (histórias) do usuário autenticado.
    
    - Lista resumida com informações básicas de cada chat
    - Ordenado por última atualização
    - Inclui título, emoji e timestamp de cada história
    """,
    responses={
        200: {"description": "Lista de chats retornada com sucesso"},
    }
)
async def get_chats(user_id: str = Depends(verify_token)):
    try:
        user = db.get_user(user_id)
        return user.chats
    except HTTPException as http_exc:
        logger.error(f"Erro ao buscar chats: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Erro ao buscar chats: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get(
    "/{chat_id}", 
    response_model=Chat, 
    status_code=200,
    summary="Obter chat específico",
    description="""
    Retorna um chat completo com todo o histórico.
    
    - Inclui todas as mensagens da história
    - Contém submissões de desenho e feedback
    - Verifica se o chat pertence ao usuário autenticado
    """,
    responses={
        200: {"description": "Chat retornado com sucesso"},
        403: {"description": "Chat não pertence ao usuário"},
        404: {"description": "Chat não encontrado"},
    }
)
async def get_chat(
    chat_id: str, 
    user_id: str = Depends(verify_token)
):
    try:
        chat = db.get_chat(chat_id, user_id) #type:ignore
        return chat
    except HTTPException as http_exc:
        logger.error(f"Erro ao buscar chat: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Erro ao buscar chat: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post(
    "/{chat_id}/submit_image", 
    response_model=SubmitImageMessage, 
    status_code=201,
    summary="Submeter desenho",
    description="""
    Permite que a criança submeta um desenho para avaliação.
    
    - Analisa se o desenho corresponde ao solicitado na história
    - Gera feedback positivo e construtivo via áudio
    - Se correto: salva a imagem e continua a história
    - Se incorreto: fornece dicas para melhorar
    
    A imagem deve estar em formato compatível (JPEG, PNG) e representar
    o elemento solicitado na última mensagem da história.
    """,
    responses={
        201: {"description": "Desenho submetido e avaliado com sucesso"},
        400: {"description": "Imagem inválida ou formato não suportado"},
        404: {"description": "Chat ou mensagem não encontrada"},
    }
)
async def submit_image_api(
    chat_id: str,
    image: UploadFile = File(..., description="Arquivo de imagem com o desenho da criança"),
    user_id: str = Depends(verify_token)
):
    try:
        chat = db.get_chat(chat_id, user_id)
        message_index = len(chat.subimits)
        
        logger.debug(f"Submetendo desenho {message_index} do chat : {chat.chat_id}")
        
        result = await submit_image(chat_id, chat.messages[-1].paint_image, image)
        
        image_path = None
        if result.is_correct:
            logger.info(f"Imagem submetida corretamente para o chat: {chat_id}, gerando nova mensagem.")
            image_path = await db.store_user_archive(user_id, image)
            feedback_audio = "Fale de uma maneira energética, elogiando o desenho da criança com essas palavras: "
            continue_chat(user_id, chat_id, message_index + 1)
        else:
            logger.info(f"Imagem submetida incorretamente para o chat: {chat_id}, gerando feedback.")
            feedback_audio = "Fale de uma maneira apasiguadora, incentivando a criança a melhorar seu desenho com essas palavras: "
            
        feedback = generate_feedback_audio(result, feedback_audio, user_id, chat_id, message_index, image_path)
        
        return feedback
    
    except HTTPException as http_exc:
        logger.error(f"Erro ao submeter imagem: {http_exc.detail}")
        raise http_exc
    
    except Exception as e:
        logger.error(f"Erro ao submeter imagem: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")