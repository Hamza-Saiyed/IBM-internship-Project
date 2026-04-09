# StudyOS — Multi-Agent AI Study Assistant

> An intelligent, multi-agent study platform powered by **Google Gemini 2.5 Flash Lite** and built with **Streamlit**.

---

## What it does

StudyOS runs a **three-agent AI pipeline** that automatically:
1. **Researches** any academic or technical topic using the Research Agent
2. **Summarizes** the findings into clean, student-friendly study notes using the Summarizer Agent
3. **Generates** a 5-question multiple-choice quiz at your chosen difficulty using the Quiz Agent

---

## Architecture

```
User Input (Topic + Difficulty)
        │
        ▼
┌──────────────────────────────────────────────────────┐
│                  Orchestrator                        │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  Research   │→ │  Summarizer  │→ │    Quiz    │  │
│  │   Agent     │  │    Agent     │  │   Agent    │  │
│  └─────────────┘  └──────────────┘  └────────────┘  │
└──────────────────────────────────────────────────────┘
        │
        ▼
   Streamlit UI
   ├── 📝 Study Notes Tab
   ├── 🧠 Interactive Quiz Tab
   └── 🔬 Raw Research Tab
```

All agents share a single `gemini_client.py` which handles:
- API key rotation across multiple keys
- Automatic retry on rate-limit errors (429 / RESOURCE_EXHAUSTED)
- Streamlit cache with 1-hour TTL to avoid redundant API calls

---

## Project Structure

```
IBM-internship-Project/
├── main.py                  # Streamlit app entry point
├── orchestrator.py          # Coordinates the three-agent pipeline
├── agents/
│   ├── gemini_client.py     # Shared Gemini API client (key rotation + retry)
│   ├── research.py          # Research Agent
│   ├── summarizer.py        # Summarizer Agent
│   └── quiz_maker.py        # Quiz Agent
├── utils/
│   ├── quiz_parser.py       # Parses LLM quiz output into structured dicts
│   └── components.py        # Streamlit UI components (quiz renderer, notes formatter)
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
└── README.md
```

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/IBM-internship-Project.git
cd IBM-internship-Project
```

### 2. Create a virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Copy `.env.example` to `.env` and add your Gemini API key(s):
```bash
cp .env.example .env
```
```env
# Single key
GEMINI_API_KEY=your_key_here

# Optional: multiple keys for rotation
GEMINI_API_KEY_1=key_one
GEMINI_API_KEY_2=key_two
```
Get a free key at [aistudio.google.com](https://aistudio.google.com).

### 5. Run the app
```bash
streamlit run main.py
```

---

## Features

| Feature | Details |
|---|---|
| 🤖 Multi-agent pipeline | Research → Summarize → Quiz, fully automated |
| 🔄 API key rotation | Automatically rotates across multiple Gemini keys on rate limits |
| 💾 Caching | Results cached for 1 hour — same topic won't re-call the API |
| 🧠 Interactive quiz | Radio-button MCQs with reveal + scoring |
| 📊 Three difficulty levels | Easy / Medium / Hard |
| 📥 Export | Download full study package or notes-only as `.txt` |
| 🔗 Share links | Shareable URL that pre-loads a topic |

---

## Tech Stack

- **Python 3.11+**
- **Streamlit** — UI framework
- **Google Gemini 2.5 Flash Lite** — LLM backbone
- **google-genai** — Official Gemini Python SDK
- **python-dotenv** — Environment variable management

---

## IBM Internship Project
Built as part of the IBM Internship Program.
