from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, WebSocket, WebSocketDisconnect, Form
from typing import List
import traceback
import asyncio
import json

from api.schemas.messages import Chat, MiniChat, SubmitImageMessage, SubmitImageHandler, Message
from api.services.chat import new_chat, continue_chat, continue_chat_async
from api.utils.logger import get_logger
from api.services.messages import submit_image, generate_feedback_audio
from api.database import db
from api.auth import verify_token, verify_token_string

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
    voice_name: str = Form(default="Kore"),
    user_id: str = Depends(verify_token)
):
    try:
        chat = await new_chat(user_id, voice_audio, voice_name) #type:ignore
        logger.info(f"Chat de Título: {chat.title} - ID: {chat.chat_id}")
        return chat
    except HTTPException as http_exc:
        logger.error(f"Erro ao criar chat: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Erro ao criar chat: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")

from api.schemas.messages import ChatsAndVoicesResponse

@router.get(
    "/", 
    response_model=ChatsAndVoicesResponse, 
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
    from api.models.core import core_model
    try:
        user = db.get_user(user_id)
        return {
            "chats": user.chats,
            "available_voices": getattr(core_model, "voice_names", ["Kore"])
        }
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
    user_id: str = Depends(verify_token),
):
    try:
        chat = db.get_chat(chat_id, user_id)  # type: ignore
        # Limita as mensagens visíveis a len(submits) + 1 para evitar expor pré-geradas indevidamente
        allowed = len(chat.subimits) + 1
        chat.messages = chat.messages[:allowed]
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
        

        result = await submit_image(chat_id, chat.messages[-1].paint_image, image, user_id)
        image_path = None
        if result.is_correct:
            logger.info(f"Imagem submetida corretamente para o chat: {chat_id}, entregando mensagem pré-processada.")
            image_path = await db.store_user_archive(user_id, image)
            feedback_audio = "Fale de uma maneira energética, elogiando o desenho da criança com essas palavras: "

            # Entregar a pending_message se existir
            pending = db.pop_pending_message(chat_id)
            if pending:
                # Adiciona a mensagem pré-processada ao chat
                db.update_chat(user_id, chat_id, 'messages', Message(**pending))
                # Iniciar geração da próxima mensagem em background
                def _generate_next():
                    try:
                        logger.info(f"Pré-processando nova mensagem para o chat: {chat_id}")
                        from api.services.messages import new_message
                        next_msg = new_message(user_id, chat_id, pending['message_index'] + 1)
                        db.set_pending_message(chat_id, next_msg.model_dump())
                        logger.info(f"Nova mensagem pré-processada salva para o chat: {chat_id}")
                    except Exception as e:
                        logger.error(f"Erro ao pré-processar nova mensagem: {e}")
                import threading
                threading.Thread(target=_generate_next, daemon=True).start()
            else:
                logger.warning(f"Nenhuma mensagem pré-processada encontrada para o chat: {chat_id}")
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

@router.get(
    "/{chat_id}/submit_image_ws/docs",
    status_code=200,
    summary="Documentação do WebSocket para submissão de desenho",
    description="""
    **📋 DOCUMENTAÇÃO DO WEBSOCKET**
    
    Este endpoint documenta como usar o WebSocket para submissão de desenhos com notificação em tempo real.
    
    **🔗 URL do WebSocket:**
    ```
    ws://localhost:8000/api/chats/{chat_id}/submit_image_ws
    ```
    
    **🎯 Propósito:**
    - Permite submissão de desenhos com feedback em tempo real
    - Se o desenho estiver correto, o usuário é notificado quando a nova parte da história estiver pronta
    - Evita a necessidade de polling ou requests adicionais
    
    **📊 Fluxo de Comunicação:**
    
    1. **Conexão**: Cliente conecta ao WebSocket
    2. **Autenticação**: Cliente envia token de autenticação
    3. **Submissão**: Cliente envia dados da imagem (base64)
    4. **Avaliação**: Servidor analisa o desenho
    5. **Feedback**: Servidor envia feedback de áudio
    6. **Continuação**: Se correto, mantém conexão e gera nova mensagem
    7. **Notificação**: Servidor envia nova mensagem quando pronta
    8. **Encerramento**: Conexão é fechada
    
    **📤 Mensagens do Cliente para Servidor:**
    
    **Autenticação:**
    ```json
    {
        "type": "auth",
        "token": "jwt_token_here"
    }
    ```
    
    **Submissão de Imagem:**
    ```json
    {
        "type": "submit_image",
        "image_data": "base64_encoded_image_data",
        "mime_type": "image/jpeg"
    }
    ```
    
    **📥 Mensagens do Servidor para Cliente:**
    
    **Feedback da Avaliação:**
    ```json
    {
        "type": "feedback",
        "message": {
            "message_index": 1,
            "audio": "path/to/feedback/audio.wav",
            "data": {
                "is_correct": true,
                "feedback": "Muito bem! Seu desenho está perfeito!"
            },
            "image": "path/to/stored/image.jpg"
        }
    }
    ```
    
    **Nova Mensagem da História (apenas se desenho correto):**
    ```json
    {
        "type": "new_message",
        "message": {
            "message_index": 2,
            "paint_image": "casa",
            "text_voice": "Era uma vez uma casa muito especial...",
            "intro_voice": "Agora desenhe uma casa!",
            "scene_image_description": "Uma bela casa colorida no campo",
            "image": "path/to/scene/image.jpg",
            "audio": "path/to/story/audio.wav"
        }
    }
    ```
    
    **Erro:**
    ```json
    {
        "type": "error",
        "message": "Descrição do erro"
    }
    ```
    
    **🔄 Estados da Conexão:**
    - **Conectado** → Aguardando autenticação
    - **Autenticado** → Aguardando imagem
    - **Processando** → Avaliando desenho
    - **Feedback enviado** → Conexão fechada (se incorreto) ou aguardando nova mensagem (se correto)
    - **Nova mensagem** → Conexão fechada
    
    **⚖️ Comparação com REST:**
    
    | Aspecto | REST `/submit_image` | WebSocket `/submit_image_ws` |
    |---------|---------------------|------------------------------|
    | **Resposta** | Apenas feedback inicial | Feedback + Nova mensagem (se correto) |
    | **Notificação** | Não | Sim, em tempo real |
    | **Polling** | Necessário | Não necessário |
    | **Complexidade** | Simples | Moderada |
    | **Experiência** | Básica | Fluída |
    
    **💡 Quando usar:**
    - **REST**: Para integrações simples ou quando WebSockets não são suportados
    - **WebSocket**: Para interfaces de usuário que precisam de notificação em tempo real
    
    **🛠️ Exemplo de Implementação JavaScript:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/chats/chat_id/submit_image_ws');
    
    ws.onopen = () => {
        // 1. Autenticar
        ws.send(JSON.stringify({
            type: 'auth',
            token: 'seu_token_aqui'
        }));
        
        // 2. Enviar imagem
        ws.send(JSON.stringify({
            type: 'submit_image',
            image_data: canvas.toDataURL().split(',')[1],
            mime_type: 'image/jpeg'
        }));
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'feedback') {
            console.log('Feedback:', data.message);
        } else if (data.type === 'new_message') {
            console.log('Nova mensagem:', data.message);
        }
    };
    ```
    
    **🔧 Ferramentas de Teste:**
    - **Postman**: Suporta teste de WebSockets
    - **wscat**: `npm install -g wscat`
    - **Browser DevTools**: Console do navegador
    """,
    responses={
        200: {"description": "Documentação do WebSocket retornada"},
    },
    tags=["WebSocket Documentation"]
)
async def get_websocket_docs(chat_id: str):
    """
    Retorna a documentação completa do WebSocket para submissão de desenhos.
    
    Este endpoint existe apenas para documentar o WebSocket correspondente,
    já que WebSockets não aparecem automaticamente no Swagger/OpenAPI.
    """
    return {
        "websocket_url": f"/api/chats/{chat_id}/submit_image_ws",
        "documentation": "Consulte a descrição completa acima para detalhes de implementação",
        "status": "WebSocket ativo e funcional",
        "alternative_rest_endpoint": f"/api/chats/{chat_id}/submit_image"
    }

@router.websocket("/{chat_id}/submit_image_ws")
@router.websocket("/{chat_id}/submit_image_ws/")
async def submit_image_websocket(
    websocket: WebSocket,
    chat_id: str
):
    """
    WebSocket endpoint para submissão de imagem com notificação em tempo real.
    
    **Fluxo de Comunicação:**
    
    1. **Conexão**: Cliente conecta ao WebSocket
    2. **Autenticação**: Cliente envia token de autenticação
    3. **Submissão**: Cliente envia dados da imagem (base64)
    4. **Avaliação**: Servidor analisa o desenho
    5. **Feedback**: Servidor envia feedback de áudio
    6. **Continuação**: Se correto, mantém conexão e gera nova mensagem
    7. **Notificação**: Servidor envia nova mensagem quando pronta
    8. **Encerramento**: Conexão é fechada
    
    **Mensagens do Cliente para Servidor:**
    ```json
    {
        "type": "auth",
        "token": "jwt_token_here"
    }
    ```
    ```json
    {
        "type": "submit_image",
        "image_data": "base64_encoded_image",
        "mime_type": "image/jpeg"
    }
    ```
    
    **Mensagens do Servidor para Cliente:**
    ```json
    {
        "type": "feedback",
        "message": {
            "message_index": 1,
            "audio": "path/to/feedback/audio.wav",
            "data": {
                "is_correct": true,
                "feedback": "Muito bem! Seu desenho está perfeito!"
            },
            "image": "path/to/stored/image.jpg"
        }
    }
    ```
    ```json
    {
        "type": "new_message",
        "message": {
            "message_index": 2,
            "paint_image": "casa",
            "text_voice": "Era uma vez...",
            "intro_voice": "Agora desenhe uma casa!",
            "scene_image_description": "Uma bela casa colorida",
            "image": "path/to/scene/image.jpg",
            "audio": "path/to/story/audio.wav"
        }
    }
    ```
    ```json
    {
        "type": "error",
        "message": "Descrição do erro"
    }
    ```
    
    **Estados da Conexão:**
    - Conectado → Aguardando autenticação
    - Autenticado → Aguardando imagem
    - Processando → Avaliando desenho
    - Feedback enviado → Conexão fechada (se incorreto) ou aguardando nova mensagem (se correto)
    - Nova mensagem → Conexão fechada
    
    **Compatibilidade:**
    Este endpoint complementa o endpoint REST `/submit_image`. 
    Clientes podem escolher usar REST (resposta única) ou WebSocket (notificação em tempo real).
    """
    
    # Aceita a conexão o quanto antes; token será verificado logo em seguida
    await websocket.accept()
    user_id = None
    
    try:
        # 1. Aguarda autenticação (primeira mensagem deve conter token)
        auth_data = await websocket.receive_json()
        
        if auth_data.get("type") != "auth":
            await websocket.send_json({
                "type": "error", 
                "message": "Primeira mensagem deve ser de autenticação"
            })
            await websocket.close()
            return
        
        # Verifica o token
        try:
            user_id = verify_token_string(auth_data.get("token"))
        except Exception:
            await websocket.send_json({
                "type": "error", 
                "message": "Token de autenticação inválido"
            })
            await websocket.close()
            return
        
        # 2. Aguarda dados da imagem
        image_data = await websocket.receive_json()
        
        if image_data.get("type") != "submit_image":
            await websocket.send_json({
                "type": "error", 
                "message": "Esperando submissão de imagem"
            })
            await websocket.close()
            return
        
        # 3. Processa a submissão da imagem
        chat = db.get_chat(chat_id, user_id)
        message_index = len(chat.subimits)
        
        logger.debug(f"WebSocket: Submetendo desenho {message_index} do chat: {chat.chat_id}")
        
        # Converte dados base64 de volta para UploadFile simulado
        import base64
        import io
        from fastapi import UploadFile
        
        image_bytes = base64.b64decode(image_data.get("image_data"))
        image_file = UploadFile(
            filename="drawing.jpg",
            file=io.BytesIO(image_bytes)
        )
        
        # Avalia o desenho
        expected_draw = chat.messages[len(chat.subimits)].paint_image
        result = await submit_image(chat_id, expected_draw, image_file, user_id)

        # 4. Processa resultado e gera feedback
        image_path = None
        if result.is_correct:
            logger.info(f"WebSocket: Imagem submetida corretamente para o chat: {chat_id}")
            image_path = await db.store_user_archive(user_id, image_file)
            feedback_audio = "Fale de uma maneira energética, elogiando o desenho da criança com essas palavras: "
        else:
            logger.info(f"WebSocket: Imagem submetida incorretamente para o chat: {chat_id}, era esperado um {expected_draw}")
            feedback_audio = "Fale de uma maneira apasiguadora, incentivando a criança a melhorar seu desenho com essas palavras: "
        
        # Gera feedback de áudio
        feedback = generate_feedback_audio(result, feedback_audio, user_id, chat_id, message_index, image_path)
        
        # 5. Envia feedback para o cliente
        await websocket.send_json({
            "type": "feedback",
            "message": {
                "message_index": feedback.message_index,
                "audio": feedback.audio,
                "data": {
                    "is_correct": result.is_correct,
                    "feedback": result.feedback
                },
                "image": feedback.image
            }
        })
        
        # 6. Se correto, usa mensagem pré-processada (pending) e dispara a próxima em background
        if result.is_correct:
            # Consumir pending message caso exista
            pending = db.pop_pending_message(chat_id)
            if pending:
                try:
                    msg = Message(**pending)
                    # Persistir a mensagem e enviar imediatamente
                    db.update_chat(user_id, chat_id, 'messages', msg)
                    await websocket.send_json({
                        "type": "new_message",
                        "message": {
                            "message_index": msg.message_index,
                            "paint_image": msg.paint_image,
                            "text_voice": msg.text_voice,
                            "intro_voice": msg.intro_voice,
                            "scene_image_description": msg.scene_image_description,
                            "image": msg.image,
                            "audio": msg.audio
                        }
                    })
                    logger.info(f"WebSocket: Nova mensagem (pending) enviada para o chat: {chat_id}")
                except Exception as e:
                    logger.error(f"WebSocket: Erro ao usar mensagem pending: {e}")
            else:
                logger.info(f"WebSocket: Sem mensagem pending; gerando nova mensagem agora para o chat: {chat_id}")
                
                # Callback para enviar nova mensagem quando pronta
                async def send_new_message(message: Message):
                    try:
                        await websocket.send_json({
                            "type": "new_message",
                            "message": {
                                "message_index": message.message_index,
                                "paint_image": message.paint_image,
                                "text_voice": message.text_voice,
                                "intro_voice": message.intro_voice,
                                "scene_image_description": message.scene_image_description,
                                "image": message.image,
                                "audio": message.audio
                            }
                        })
                        logger.info(f"WebSocket: Nova mensagem enviada para o chat: {chat_id}")
                    except Exception as e:
                        logger.error(f"WebSocket: Erro ao enviar nova mensagem: {e}")
                
                # Gera nova mensagem de forma assíncrona
                _ = await continue_chat_async(user_id, chat_id, message_index + 1, send_new_message)

            # Iniciar geração da próxima pending em background
            import threading
            from api.services.messages import new_message as generate_new_message
            def _prefetch_next():
                try:
                    next_index = message_index + 1 if not pending else pending.get('message_index', message_index) + 1
                    logger.info(f"WebSocket: Pré-processando próxima mensagem {next_index} para o chat: {chat_id}")
                    next_msg = generate_new_message(user_id, chat_id, next_index)
                    db.set_pending_message(chat_id, next_msg.model_dump())
                    logger.info(f"WebSocket: Próxima mensagem pré-processada salva para o chat: {chat_id}")
                except Exception as e:
                    logger.error(f"WebSocket: Erro ao pré-processar próxima mensagem: {e}")
            threading.Thread(target=_prefetch_next, daemon=True).start()
        
        # 7. Fecha conexão
        await websocket.close()
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket: Cliente desconectou do chat: {chat_id}")
    
    except Exception as e:
        logger.error(f"WebSocket: Erro durante submissão de imagem: {e}")
        logger.error(traceback.format_exc())
        
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Erro interno do servidor"
            })
            await websocket.close()
        except:
            pass