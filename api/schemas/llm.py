from pydantic import BaseModel, Field
from typing import Optional

class ContinueChat(BaseModel):
    """
    Resposta do LLM para continuação de chat.
    
    Contém todos os elementos necessários para criar uma nova interação
    na história: texto narrado, imagem para desenhar e descrição da cena.
    """
    paint_image: str = Field(
        description="Nome do objeto que deverá ser gerada uma imagem para a criança desenhar/colorir, de modo que seja um desenho simples que a criança possa colorir. E que seja algo principal que tenha na história descrição da imagem."
    )
    text_voice: str = Field(
        description="Texto que deverá ser lido para a criança, crie um texto não muito longo, de até 100 palavras"
    )
    intro_voice: str = Field(
        description="Trecho que será a introdução para iteração da criança, deverá ser um trecho curto de até 10 palavras, que introduza o que a criança deverá desenhar nessa etapa"
    )
    scene_image_description: str = Field(
        description="Descrição da cena que ilustra a cena da história que está sendo contada"
    )

class NewChat(ContinueChat):
    """
    Resposta do LLM para início de novo chat.
    
    Herda de ContinueChat e adiciona metadados específicos para
    inicialização: título da história e emoji representativo.
    """
    title: str = Field(
        description="Título da história, deve ser usado para dar um nome à história que está sendo contada."
    )
    shortcode: str = Field(
        description="Shortcode que referencia um emoji, que remeta a um elemento da história que está sendo contada, como por exemplo :art:"
    )

class SubmitImageResponse(BaseModel):
    """
    Resposta do LLM para análise de desenho submetido.
    
    Contém avaliação se o desenho está correto e feedback
    apropriado para a criança.
    """
    is_correct: bool = Field(
        description="Se o desenho está correto ou não, ou seja, se o desenho representa o que foi pedido na história."
    )
    feedback: str = Field(
        description="Feedback para a criança, caso o desenho esteja correto, você pode elogiar o desenho e dizer que ela fez um ótimo trabalho. Caso o desenho não esteja correto, você deve dizer que o desenho não está correto e dar dicas de como melhorar o desenho, mas sempre de forma positiva e incentivadora."
    )

class SubmitImageAPIResponse(SubmitImageResponse):
    """
    Resposta da API para submissão de imagem.
    
    Herda de SubmitImageResponse e adiciona o caminho do arquivo
    de feedback gerado.
    """
    feedback_path: str = Field(
        description="Caminho da imagem submetida pelo usuário, para ser usada na validação do desenho."
    )

class AssertContinueChat(BaseModel):
    is_correct: bool = Field(
        description="Verifica se a continuação do chat está correta ou não, ou seja, se não foi solicitado um desenho que a criança já desenhou anteriormente."
    )
    feedback: str = Field("Feedback para um modelo de IA sobre a continuação do chat, sobre o que ele deverá fazer para corrigir a continuação da história solicitada")