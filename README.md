# Smart Recipe Generator

A modern AI-powered recipe assistant leveraging RAG (Retrieval Augmented Generation) technology. This application helps you discover, understand, and customize recipes based on your ingredients and preferences.

## Features

- **Recipe Search**: Find recipes based on available ingredients
- **Smart Chat**: Ask questions about cooking techniques and recipes
- **Recipe Scaling**: Automatically adjust ingredient quantities
- **Similar Recipe Suggestions**: Discover alternatives to your favorite dishes
- **Intuitive UI**: Clean Streamlit interface with conversation history

## Requirements

- Python 3.9+
- Ollama (for running local LLM models)
- CUDA-capable GPU (optional, for improved performance)

## Installation

### 1. Install Ollama

Ollama is required to run the local LLM models used by this application.

#### macOS

```bash
brew install ollama
```

#### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### Windows

Download and install from the [Ollama website](https://ollama.com/download/windows).

### 2. Create a Virtual Environment (Recommended)

Creating a virtual environment helps isolate dependencies for this project.

#### Using venv (Python's built-in module)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

#### Using conda

```bash
# Create conda environment
conda create -n recipe-gen python=3.9
# Activate environment
conda activate recipe-gen
```

### 3. Install Python Dependencies

With your virtual environment activated:

For systems with CUDA-capable GPUs:

```bash
pip install -r requirements_cuda.txt
```

For CPU-only systems (macOS, Windows, Linux without CUDA):

```bash
pip install -r requirements_mi.txt
```

### 4. Download Required Models

Before running the application, you need to download the required LLM models:

```bash
# Main model for recipe generation
ollama pull qwen:7b

# Lightweight model for query classification
ollama pull tinyllama:1.1b

# Embedding model for semantic search
ollama pull nomic-embed-text
```

## Usage

This project provides two independent interfaces: a Streamlit web UI and a FastAPI backend service. You can choose to run either one or both, depending on your needs. The Streamlit UI does not require the API service to be running, and vice versa.

### Streamlit UI (Recommended)

Launch the application with:

```bash
streamlit run vision3.py
```

Then open your browser at `http://localhost:8501` to access the interface.

### API Service

To run the API service instead of the Streamlit UI:

```bash
# Start Ollama in the background if not already running
ollama serve &

# Start the FastAPI server
python -m uvicorn app:app --reload --port 8000
```

Once running, you can:

- Access the API documentation at `http://localhost:8000/docs`
- Make API calls to endpoints like `http://localhost:8000/query`

Sample API call using curl:

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I make scrambled eggs?"}'
```

## How It Works

The application uses a combination of:

1. **Vector Search**: Recipes are embedded in a vector space for semantic retrieval
2. **LLM Processing**: Local language models process your queries and generate responses
3. **Query Classification**: Automatically detects the intent behind your questions
4. **Contextual Memory**: Maintains conversation context for natural interactions

## API Reference

This project provides both a Streamlit UI and API endpoints for integration:

| Endpoint          | Method | Description                            |
| :---------------- | :----- | :------------------------------------- |
| `/query`          | POST   | Single-turn question answering         |
| `/chat`           | POST   | Multi-turn conversation with memory    |
| `/keyword_search` | POST   | Search based on keyword extraction     |
| `/suggest`        | POST   | Recommend recipes based on ingredients |
| `/similar`        | POST   | Find similar recipes                   |
| `/scale`          | POST   | Scale ingredient quantities            |

### Generating the Index (Recommended for Better Performance)

Instead of building the index on each startup (which can be time-consuming), you can pre-generate the index:

```bash
# Generate the index (only needed once or when the recipe data changes)
python generate_index.py
```

This will create an index storage in the `data/index_storage` directory. The application will automatically use this pre-built index when available, significantly reducing startup time.

The index is already generated, so you don't need to run the above command.
