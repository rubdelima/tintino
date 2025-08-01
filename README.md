## 🐠 Tintino – Histórias Interativas com Inteligência Artificial


> **Objetivo**: Tornar a tecnologia uma aliada para histórias, estimulando a criatividade, a imaginação e a autonomia das crianças através de um ambiente lúdico, educativo e interativo.

<p align="center">
  <img src="./assets/images/logo.png" alt="estuda-ai" width="60%">
</p>


**Tintino** é um projeto desenvolvido para a disciplina de **Criatividade Computacional**, com o propósito de explorar o uso de **Inteligência Artificial** na criação de histórias **interativas e personalizadas para crianças**.

A proposta do projeto é transformar a experiência de contar histórias em algo mais **imaginativo, dinâmico e multimodal**, por meio de:

🎨 **Imagens Geradas por IA**: as cenas e personagens são criados a partir de prompts, trazendo ilustrações únicas e encantadoras.

🎙️ **Narração por Voz**: com uso de síntese de voz, as histórias ganham vida por meio de áudios expressivos e imersivos.

🗣️ **Interações por Fala e Escuta**: a criança pode participar das histórias, fazendo escolhas, respondendo perguntas e interagindo com os personagens por voz.

🖍️ **Avaliação de Desenhos**: o sistema também incentiva a criatividade ao permitir que a criança desenhe e receba um retorno gentil da IA, incentivando a expressão artística.

## Configurando o ambiente

Recomendamos criar um ambiente virtual para isolar as dependências do projeto. Você pode usar **Conda** ou **venv**:

### Usando Conda

```bash
conda create -n louie python=3.10.6
conda activate louie
```

### Usando venv

```bash
python3 -m venv .venv
# Linux/macOS
echo "source .venv/bin/activate"
# Windows
# .venv\Scripts\activate
```

## Instalação das dependências

Dependendo do seu hardware, instale as dependências a partir do arquivo apropriado:

* **Com GPU NVIDIA (CUDA):**

  ```bash
  pip install -r requirements/api_nvidia.txt
  ```

* **Sem CUDA (CPU):**

  ```bash
  pip install -r requirements/api.txt
  ```

* **Usar Whisper Via API apenas:**

  ```bash
  pip install -r requirements/api.txt
  ```

Instalar o ffmpeg, se usar o conda : ... 

## Configuração de variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto e adicione sua chave da API do Google Gemini e da OpenAI (para usar o whisper via API):

```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY= your_openai_api_key_here
```

## Executando a API

Para iniciar o servidor da API em modo de desenvolvimento com recarga automática:

```bash
uvicorn api.main:app --reload
```

## Ver o Protótipo da Interface

Para ver o protótipo, primeiramente instale as dependências para a Interface, você pode instalar as dependências com:

```bash
pip install -r requirements/st.txt
```

Primeiramente inicie o servidor da api na porta 8000, depois você pode inicir a parte visual com o comando:

```bash
streamlit run streamlit_app.py
```

A API ficará disponível em `http://localhost:8000`.
O UI ficará disponível em `http://localhost:8501`

---
