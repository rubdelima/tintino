# Louie

## Sobre o Projeto

Louie é um projeto da disciplina de Criatividade Computacional com o objetivo de criar histórias interativas para crianças, utilizando imagens e áudio gerados por ferramentas de Inteligência Artificial. Através de prompts, o sistema gera elementos visuais e narrativos que tornam a experiência mais envolvente e personalizada.

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
