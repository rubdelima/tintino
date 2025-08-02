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

## 🚀 Formas de Executar o Projeto

### 🐳 Usando Docker (Recomendado para Produção)

A forma mais simples de executar o projeto completo é utilizando Docker Compose:

**Execução com logs visíveis (modo tradicional):**
```bash
docker-compose up --build
```

**Execução em segundo plano (background):**
```bash
docker-compose up --build -d
```

**Para acompanhar os logs quando executando em background:**
```bash
docker-compose logs -f
```

**Para parar os containers:**
```bash
docker-compose down
```

**Acesso:**
- **Frontend (Interface)**: `http://localhost`
- **API**: `http://localhost/api`
- **Documentação da API**: `http://localhost/api/docs` ou `http://localhost/api/redoc`

> **⚠️ Nota**: O Docker é excelente para deploy e execução completa, mas no Windows pode consumir mais recursos devido à virtualização. Para desenvolvimento, ou recursos limitados, considere a execução manual da API.

### 🛠️ Execução Manual (Recomendado para Desenvolvimento)

#### 1. Configurando o ambiente

Recomendamos criar um ambiente virtual para isolar as dependências do projeto, de preferência com o conda:

**Usando Conda:**
```bash
conda create -n louie python=3.10.6
conda activate louie
```

**Usando venv:**
```bash
python3 -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

#### 2. Instalação das dependências

As dependências do projeto estão **organizadas por componente** na pasta `requirements/` para facilitar a instalação apenas do que você precisa:

**Para a API (Backend):**

A API é o núcleo do sistema que processa as requisições e se comunica com os modelos de IA. 

**Primeiro, instale as dependências principais:**
```bash
pip install -r requirements/api.txt
```

**Depois, se quiser usar modelos locais, instale uma das extensões:**
```bash
# Para usar Whisper local com GPU NVIDIA + CUDA (processamento local mais rápido)
pip install -r requirements/api_nvidia.txt

# Para usar Whisper local apenas com CPU (processamento local mais lento)
pip install -r requirements/api-cpu.txt
```

> **⚠️ Importante**: 
> - O `api.txt` contém todas as dependências básicas e permite usar Whisper via API da OpenAI (recomendado)
> - Os outros arquivos (`api_nvidia.txt` e `api-cpu.txt`) contêm apenas Whisper e PyTorch para execução local
> - Para usar Whisper via API: configure a chave `OPENAI_API_KEY` no arquivo `.env`
> - Para usar Whisper local: configure `use_api = false` no arquivo `config.toml`

**Para a Interface (Frontend):**

A interface é a parte visual do projeto (Streamlit) que os usuários vão interagir:

```bash
pip install -r requirements/st.txt
```

> **💡 Dica**: Se você for desenvolver ou usar ambos (API + Interface), instale as duas dependências. Se for apenas testar a API, instale apenas a primeira.

#### 3. Dependências do Sistema

**📦 FFmpeg (Obrigatório):**

- **Linux**: `sudo apt install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows/Conda**: `conda install ffmpeg`

**🪄 Python Magic:**

- **Windows**: Use `python-magic-bin` em vez de `python-magic`:
  ```bash
  pip install python-magic-bin
  ```
  > O `python-magic-bin` já inclui as dependências binárias necessárias para Windows.

- **Linux/macOS**: O `python-magic` padrão funciona corretamente.

#### 4. Configuração de variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com suas chaves de API:

```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

> **💡 Dica**: Existe um arquivo `env.example` na raiz do projeto que você pode usar como modelo. Basta copiá-lo para `.env` e preencher com suas chaves.

#### 5. Executando os serviços

**API (Backend):**
```bash
uvicorn api.main:app --reload
```

**Interface (Frontend):**
```bash
streamlit run streamlit_app.py
```

**Acesso:**
- **API**: `http://localhost:8000`
- **Documentação da API**: `http://localhost:8000/docs`
- **Interface**: `http://localhost:8501`

---
