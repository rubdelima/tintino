import os
from api.schemas.messages import NewChatInput, Chat
from api.utils.logger import get_logger
from api.models.speech_to_text import transcribe_audio
import uuid
from api.utils import load_json, save_json
import time
from api.services.messages import new_message, generate_next_message
import threading
import os
logger = get_logger(__name__)

os.makedirs('./temp', exist_ok=True)

chats = {
    dir_name : Chat(**load_json(os.path.join('./temp', dir_name, 'chat.json')))
    for dir_name in os.listdir('./temp')
    if os.path.exists(os.path.join('./temp', dir_name, 'chat.json'))
}

def new_chat(input_data: NewChatInput) -> Chat:
    chat_id = str(uuid.uuid4())
    os.makedirs(f'./temp/{chat_id}', exist_ok=True)
    
    logger.debug(f"Criando novo chat com ID: {chat_id}")
    
    assert (input_data.instruction is not None) or (input_data.audio_path is not None), "You must provide either an instruction or an audio path."
    
    if input_data.audio_path:
        assert os.path.exists(input_data.audio_path), f"Audio file {input_data.audio_path} does not exist."
        
        logger.debug(f"Extraindo texto do áudio: {input_data.audio_path}")
        start_time = time.time()
        input_data.instruction = transcribe_audio(input_data.audio_path)
        logger.debug(f"Transcrição concluída em {time.time() - start_time:.2f} segundos.")
    
    message = new_message(input_data.instruction, chat_id, 0)
    
    chat = Chat(
        chat_id=chat_id,
        title=message.data.title if message.data.title else "Nova História",
        messages=[message],
        submit_image_messages=[]
    )
    
    logger.debug(f"Novo chat criado com ID: {chat_id} e título: {chat.title}")
    
    save_json(f'./temp/{chat_id}/chat.json', chat.model_dump())
    
    chats[chat_id] = chat
    
    return chat

def continue_chat(chat_id: str):
    """
    Continua o chat gerando a próxima mensagem de forma assíncrona
    """
    def _continue_chat_async():
        try:
            chat = chats.get(chat_id)
            if not chat:
                logger.error(f"Chat {chat_id} não encontrado")
                return
            
            logger.info(f"Gerando próxima mensagem para o chat: {chat_id}")
            
            message = generate_next_message(
                chat_id=chat_id,
                message_id=len(chat.messages),
                history=[msg.data.text_voice for msg in chat.messages],
                paintned_items=", ".join([msg.data.paint_image for msg in chat.messages]),
                last_image=chat.messages[-1].image
            )
            
            chats[chat_id].messages.append(message)
            
            save_json(f'./temp/{chat_id}/chat.json', chats[chat_id].model_dump())
            
            logger.info(f"Próxima mensagem gerada com sucesso para o chat: {chat_id}")
            
        except Exception as e:
            logger.error(f"Erro ao continuar chat {chat_id}: {str(e)}")
    
    thread = threading.Thread(target=_continue_chat_async, daemon=True)
    thread.start()
    
    logger.info(f"Iniciando geração assíncrona da próxima mensagem para o chat: {chat_id}")