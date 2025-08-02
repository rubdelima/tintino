from pydantic import BaseModel, Field
from typing import List
from api.schemas.messages import MiniChat

class CreateUser(BaseModel):
    """
    Schema para criação de usuário.
    
    Usado quando um novo usuário é criado no sistema.
    Requer apenas o nome, pois a autenticação é feita via Firebase Auth.
    """
    name: str = Field(
        ...,
        description="Nome completo do usuário",
        min_length=2,
        max_length=50,
        examples=["Maria Silva", "João Santos", "Ana Costa"]
    )

class UserDB(BaseModel):
    """
    Schema de usuário armazenado no banco de dados.
    
    Contém informações básicas do usuário após criação.
    O user_id é o Firebase UID ou UUID interno dependendo da configuração.
    """
    user_id: str = Field(
        ...,
        description="ID único do usuário (Firebase UID ou UUID interno)",
        examples=["f4b7b9e2-b26a-480a-ac43-0e085482390f", "abc123xyz789"]
    )
    name: str = Field(
        ...,
        description="Nome completo do usuário",
        examples=["Maria Silva", "João Santos"]
    )

class User(UserDB):
    """
    Schema completo de usuário com informações relacionadas.
    
    Retornado nas APIs que precisam de informações completas do usuário,
    incluindo a lista de chats associados.
    """
    chats: List[MiniChat] = Field(
        default=[],
        description="Lista de chats (histórias) do usuário"
    )