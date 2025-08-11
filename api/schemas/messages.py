from pydantic import BaseModel, Field
from typing import List

# ...existing code...


# Resposta customizada para GET /api/chats/
class ChatsAndVoicesResponse(BaseModel):
    chats: List['MiniChat']
    available_voices: List[str]
from pydantic import BaseModel, Field
from api.schemas.llm import ContinueChat, SubmitImageResponse
from typing import List, Optional
from datetime import datetime

class ChatItems(BaseModel):
    """
    Itens de contexto de um chat para processamento.
    
    Contém o histórico formatado e informações sobre elementos 
    já desenhados para dar contexto ao modelo de IA.
    """
    history: str = Field(
        ...,
        description="Histórico completo das mensagens do chat",
        examples=["Era uma vez um dragão que adorava pintar..."]
    )
    painted_items: str = Field(
        ...,
        description="Lista de itens já desenhados pela criança",
        examples=["dragão, castelo, floresta"]
    )
    last_image: str = Field(
        ...,
        description="Caminho da última imagem enviada",
        examples=["/temp/images/dragon_sketch.png"]
    )

class NewChatInput(BaseModel):
    """
    Entrada para criação de novo chat.
    
    Pode ser iniciado via áudio (transcrito) ou instrução de texto direta.
    Usado internamente pelos serviços de chat.
    """
    audio_path: Optional[str] = Field(
        None,
        description="Caminho do arquivo de áudio",
        examples=["/temp/audio/story_request.wav"]
    )
    instruction: Optional[str] = Field(
        None,
        description="Instrução de texto alternativa",
        examples=["Quero uma história sobre dinossauros"]
    )

class Message(ContinueChat):
    """
    Mensagem completa em um chat.
    
    Herda de ContinueChat e adiciona metadados específicos da mensagem,
    como índice sequencial e caminhos de arquivos.
    """
    message_index: int = Field(
        ...,
        description="Índice sequencial da mensagem no chat",
        ge=0,
        examples=[0, 1, 2]
    )
    image: str = Field(
        ...,
        description="Caminho da imagem de referência para desenho",
        examples=["/temp/images/dragon_outline.png"]
    )
    audio: str = Field(
        ...,
        description="Caminho do arquivo de áudio da resposta",
        examples=["/temp/audio/story_part1.mp3"]
    )

class SubmitImageMessage(BaseModel):
    """
    Resposta de submissão de desenho.
    
    Retornada quando uma criança submete um desenho,
    contém feedback e análise da correção.
    """
    message_index: int = Field(
        ...,
        description="Índice da mensagem relacionada",
        ge=0,
        examples=[0, 1, 2]
    )
    audio: str = Field(
        ...,
        description="Caminho do áudio de feedback",
        examples=["/temp/audio/feedback_positive.mp3"]
    )
    image: Optional[str] = Field(
        None,
        description="Caminho da imagem submetida (se correta)",
        examples=["/temp/images/child_dragon_drawing.png"]
    )
    data: SubmitImageResponse = Field(
        ...,
        description="Análise detalhada da submissão"
    )

class MiniChatBase(BaseModel):
    """
    Informações básicas de um chat.
    
    Estrutura base para representação simplificada de chats
    em listagens e referencias.
    """
    title: str = Field(
        ...,
        description="Título gerado automaticamente do chat",
        max_length=100,
        examples=["A Aventura do Dragão Artista", "O Castelo Mágico"]
    )
    chat_image: str = Field(
        ...,
        description="Emoji/ícone representativo do chat",
        examples=["🐉", "🏰", "🦄", "🌟"]
    )
    last_update: datetime = Field(
        ...,
        description="Última atualização do chat"
    )
    voice_name: str = Field(
        default="Kore",
        description="Nome da voz utilizada para narração do chat",
        examples=["Kore", "sage", "shimmer"]
    )

class MiniChat(MiniChatBase):
    """
    Chat resumido com ID.
    
    Versão compacta do chat para listagens e navegação.
    Contém apenas informações essenciais.
    """
    chat_id: str = Field(
        ...,
        description="ID único do chat",
        examples=["chat_123abc", "story_456def"]
    )

class Chat(MiniChat):
    """
    Chat completo com todo o histórico.
    
    Contém todas as mensagens e submissões de imagem do chat.
    Usado para visualização completa da conversa.
    """
    messages: List[Message] = Field(
        default=[],
        description="Lista completa de mensagens"
    )
    subimits: List[SubmitImageMessage] = Field(
        default=[],
        description="Lista de submissões de desenho"
    )
    # voice_name já herdado de MiniChatBase

class SubmitImageHandler(BaseModel):
    """
    Handler para submissão de imagem.
    
    Usado internamente para processar submissões de desenho
    e gerar feedback adequado.
    """
    chat_id: str = Field(
        ...,
        description="ID do chat relacionado",
        examples=["chat_123abc"]
    )
    message_id: int = Field(
        ...,
        description="ID da mensagem relacionada",
        ge=0,
        examples=[0, 1, 2]
    )
    image_path: str = Field(
        ...,
        description="Caminho da imagem submetida",
        examples=["/temp/uploads/drawing.png"]
    )

