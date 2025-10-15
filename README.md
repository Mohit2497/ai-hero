# Repo Assistant

[![Python version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🎬 Demo

![Repo Assistant demo](./repo_assistant.gif)

## 🤖 Project Overview

This project implements a comprehensive Retrieval-Augmented Generation (RAG) system for Microsoft's AI Agents for Beginners documentation. It processes the [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) repository, creating an intelligent AI assistant that can answer questions about Microsoft's AI agent framework, setup guides, best practices, and troubleshooting through natural language interaction.

**Key Achievement**: Transitioned from experimental Jupyter notebooks to a production-ready web application with proper modular architecture, rate limiting, and persistent state management.

## ✨ Key Features

- 🌐 **Interactive Web Interface**: Streamlit application with conversation context control
- 📚 **Comprehensive Documentation Coverage**: Processes Microsoft's entire AI Agents for Beginners course
- 🧩 **Advanced Chunking Strategies**: Sliding window and intelligent chunking with configurable parameters
- 🔍 **Hybrid Search System**: Combines text, vector, and hybrid search using minsearch
- 🤖 **Pydantic AI Agent**: Intelligent agent with search tool integration for contextual Q&A
- 🎯 **Smart Rate Limiting**: Sophisticated rate limiting for Gemini API free tier (15 RPM, 1M TPM, 1500 RPD)
- 💾 **Persistent State Management**: Maintains rate limit state and conversation history across sessions
- ⚡ **Optimized Performance**: Pre-built index caching for instant loading on Streamlit Cloud
- 📊 **LLM-as-Judge Evaluation**: Comprehensive evaluation system with structured assessment

## 📋 Requirements

- Python 3.11+
- Google AI API key (for Gemini models - free tier supported)
- Dependencies listed in `requirements.txt`

## 🚀 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ms-ai-agents-assistant.git
   cd ms-ai-agents-assistant
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

5. **Build the search index** (optional but recommended for faster startup):
   ```bash
   python scripts/build_index.py
   ```
   This pre-builds the index locally to avoid 60-90 second processing time on each app restart.

## 💻 Usage

### Web Interface (Streamlit)

1. **Run the application**:
   ```bash
   streamlit run app.py
   ```

2. **Access the interface**:
   - Open your browser and navigate to `http://localhost:8501`
   - Ask questions about Microsoft AI Agents in natural language
   - View rate limit statistics in the sidebar

3. **Features available**:
   - 💬 Natural language Q&A about AI agents
   - 📎 Automatic source citations with GitHub links
   - 🔄 Toggle between contextual and independent questions
   - 📊 Real-time rate limit monitoring
   - 🗑️ Clear chat history option

### Command Line Interface

For development and testing:

```python
from app import ingest, search_agent

# Initialize the index
index = ingest.index_data(
    repo_owner="microsoft",
    repo_name="ai-agents-for-beginners",
    chunk=True,
    chunking_params={'size': 2000, 'step': 1000}
)

# Initialize the agent
agent = search_agent.init_agent(index, "microsoft", "ai-agents-for-beginners")

# Ask questions
response = agent.run_sync("What are AI agents?")
print(response.data)
```

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────┐
│         Streamlit Web Interface         │
├─────────────────────────────────────────┤
│          Rate Limiter Module            │
├─────────────────────────────────────────┤
│         Pydantic AI Agent               │
├─────────────────────────────────────────┤
│          Search Tools Layer             │
├─────────────────────────────────────────┤
│    Document Processing & Indexing       │
├─────────────────────────────────────────┤
│      GitHub Repository Ingestion        │
└─────────────────────────────────────────┘
```

### Core Modules

- **`ingest.py`**: Document ingestion and processing pipeline
  - Repository downloading and extraction
  - Frontmatter metadata parsing
  - Sliding window chunking implementation
  - Index creation with minsearch

- **`search_agent.py`**: AI agent initialization and configuration
  - System prompt template
  - Gemini model integration
  - Tool registration

- **`search_tools.py`**: Search functionality
  - Text-based search interface
  - Index query execution
  - Result ranking and filtering

- **`app.py`**: Streamlit application
  - Interactive UI components
  - Rate limiting implementation
  - Conversation state management
  - Async streaming responses

- **`logs.py`**: Interaction logging system
  - Structured log entries
  - JSON serialization
  - File-based persistence

### Rate Limiting System

Sophisticated rate limiting designed for Gemini API free tier constraints:

- **Limits enforced**:
  - 10 requests per minute (RPM)
  - 1,000,000 tokens per minute (TPM)
  - 1,500 requests per day (RPD)

- **Features**:
  - Exponential backoff for frequent requests
  - Persistent state across application restarts
  - Visual progress indicators in UI
  - Automatic cleanup of old request timestamps

## 📊 Evaluation System

The project includes comprehensive evaluation capabilities:

1. **Test Data Generation**: Automated question generation from documentation
2. **LLM-as-Judge**: Structured evaluation criteria including:
   - Instructions adherence
   - Answer relevance and clarity
   - Citation accuracy
   - Tool usage verification
3. **Logging System**: Complete interaction tracking for analysis

## 🛠️ Development

### Project Structure

```
ms-ai-agents-assistant/
├── app/
│   ├── __init__.py
│   ├── ingest.py         # Document processing
│   ├── search_agent.py   # Agent configuration
│   ├── search_tools.py   # Search implementation
│   └── logs.py           # Logging utilities
├── scripts/
│   └── build_index.py    # Pre-build index script
├── data/
│   └── ms_ai_agents_index.pkl  # Cached index
├── logs/                 # Interaction logs
├── app.py               # Main Streamlit app
├── requirements.txt
├── .env.example
└── README.md
```

### Running Tests

```bash
# Run evaluation
python -m pytest tests/

# Check code quality
flake8 app/
black app/ --check
```

## 📈 Development Roadmap

### ✅ Completed (Days 1-6)
- [x] **Day 1**: Data ingestion and indexing from GitHub
- [x] **Day 2**: Multiple chunking strategies implementation
- [x] **Day 3**: Hybrid search with text and vector capabilities
- [x] **Day 4**: Pydantic AI agent with search tool integration
- [x] **Day 5**: Evaluation system with LLM-as-judge
- [x] **Day 6**: Web deployment with Streamlit

### 🔄 Current Challenges
- [ ] Debug search tool invocation for technical questions
- [ ] Optimize response consistency
- [ ] Improve context-aware responses

### 🚀 Future Enhancements
- [ ] Add vector embeddings with sentence transformers
- [ ] Implement semantic search capabilities
- [ ] Add conversation export functionality
- [ ] Enhance evaluation metrics dashboard
- [ ] Implement multi-language support

## 🔧 Troubleshooting

### Common Issues

1. **Rate limit errors**:
   - Solution: Wait for the cooldown period shown in the UI
   - The app implements automatic exponential backoff

2. **Index building takes too long**:
   - Solution: Run `python scripts/build_index.py` to pre-build
   - This creates a cached index for instant loading

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Microsoft for the [AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) repository
- [AI Agents Bootcamp](https://alexeygrigorev.com/aihero/) by Alexey Grigorev
- Google for the Gemini API free tier
- The Pydantic AI and Streamlit communities

---

**Note**: This project is part of the AI Agents Bootcamp and demonstrates production-ready RAG system implementation with modern Python tools and best practices.