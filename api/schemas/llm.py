from pydantic import BaseModel, Field
from typing import Optional

class ChatResponse(BaseModel):
    title : Optional[str] = Field(default=None, description="Título da história, opcional, pode ser usado para dar um nome à história que está sendo contada.")
    paint_image  : str = Field(description="Nome do objeto (em inglês) que deverá ser gerada uma imagem para a criança desenhar/colorir, de modo que seja um doodle disponível na base de dados do Doodle Maker, ou seja, um desenho simples que a criança possa colorir. Exemplo: 'cat', 'dog', 'house', 'tree', etc.")
    text_voice : str = Field(description="Texto que deverá ser lido para a criança, crie um texto não muito longo, de até 100 palavras")
    intro_voice : str = Field(description="Trecho que será a introdução para iteração da crinaça, deverá ser um trecho curto de até 10 palavras")
    scene_image_description : str = Field(description="Descrição da cena que ilusta a cena da história que está sendo contada")
    
class SubmitImageResponse(BaseModel):
    is_correct: bool = Field(description="Se o desenho está correto ou não, ou seja, se o desenho representa o que foi pedido na história.")
    feedback: str = Field(description="Feedback para a criança, caso o desenho esteja correto, você pode elogiar o desenho e dizer que ela fez um ótimo trabalho. Caso o desenho não esteja correto, você deve dizer que o desenho não está correto e dar dicas de como melhorar o desenho, mas sempre de forma positiva e incentivadora.")

class SubmitImageAPIResponse(SubmitImageResponse):
    feedback_path : str = Field(description="Caminho da imagem submetida pelo usuário, para ser usada na validação do desenho.")