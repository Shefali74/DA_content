# Resume Roast Agent - AI Agents 101 Demo

Build your own AI agent that reads resumes, searches live job postings, and delivers brutally honest feedback. In ~25 lines of Python.

## Quick Setup (5 minutes)

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate    # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure credentials (pick ONE)

# Option A: AWS Bedrock (default - uses Claude)
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"

# Option B: Ollama (FREE - no cloud needed!)
# Install Ollama:
#   Mac:     brew install ollama
#   Windows: Download from https://ollama.com/download
#   Linux:   curl -fsSL https://ollama.com/install.sh | sh
#
# Pull a model:
#   ollama pull llama3.1:8b
#
# Then use agent_ollama.py instead


# 4. Run the agent!
python agent.py
```

## Files

| File | What it does |
|------|-------------|
| `agent.py` | Main agent - uses Bedrock (Claude) |
| `agent_ollama.py` | Same agent but uses Ollama (FREE, local) |
| `sample_resume.txt` | Fake resume with obvious gaps (for demo) |
| `requirements.txt` | Dependencies |

## How It Works

```
Agent = Model + Tools + Prompt

Model:  Claude (via Bedrock) or Llama (via Ollama)
Tools:  file_read + http_request
Prompt: "You are a brutally honest resume reviewer..."
```

The agent autonomously:
1. Reads the resume (file_read tool)
2. Extracts skills and experience
3. Searches live job postings (http_request tool)
4. Compares your skills vs market demand
5. Delivers specific, actionable roast

## Challenge: Make It Yours

Fork this and try:
- Resume Roast Agent (what we built)
- GitHub Profile Analyzer
- Hackathon Idea Generator
- Study Planner Agent
- Price Tracker Agent

The framework is the same - just change the `system_prompt` and `tools`.

## Ollama Setup (All Platforms - FREE)

| Platform | Install Command |
|----------|----------------|
| **Mac** | `brew install ollama` or download from [ollama.com](https://ollama.com/download) |
| **Windows** | Download installer from [ollama.com/download](https://ollama.com/download) |
| **Linux** | `curl -fsSL https://ollama.com/install.sh | sh` |

After installing:
```bash
# Pull the model (one-time download ~4GB)
ollama pull llama3.1:8b

# Run the free version
python agent_ollama.py
```

## Adding Custom Tools

```python
from strands import Agent, tool

@tool
def search_naukri(role: str, location: str) -> str:
    """Search Naukri.com for job postings.
    
    Args:
        role: Job role to search for
        location: City/location
    """
    # Your logic here
    import requests
    # ... fetch from Naukri API or scrape
    return results

# Add to your agent
agent = Agent(
    tools=[search_naukri, file_read, http_request],
    system_prompt="..."
)
```

## Resources

- [Strands Agents Docs](https://strandsagents.com)
- [Strands GitHub](https://github.com/strands-agents)
- [Ollama](https://ollama.com) - Free local models
- [Examples](https://strandsagents.com/docs/examples/)
