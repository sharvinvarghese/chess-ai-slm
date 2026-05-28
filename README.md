# ♟ Chess AI SLM

> Play chess against a minimax engine while a local SLM trash-talks you in character — no cloud required (except optional Gemini hints).

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-black?style=flat-square&logo=flask)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## What is this?

A **fully local chess web app** with three independent layers:

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (Flask)                     │
├───────────────┬─────────────────┬───────────────────────┤
│  Chess Engine │   Personality   │      LLM Hints        │
│  python-chess │   SmolLM2 (SLM) │  Gemini Flash Lite    │
│  + minimax    │   Rex persona   │  (optional, H key)    │
│  100% local   │   100% local    │  cloud, key required  │
└───────────────┴─────────────────┴───────────────────────┘
```

| Layer | Responsibility | Cloud? |
|---|---|---|
| **python-chess + minimax** | Legal moves, AI opponent (Black), check/mate | ❌ Never |
| **SmolLM2 SLM** | Rex's trash talk + chat replies | ❌ Never |
| **Gemini Flash Lite** | On-demand coaching hints (`H` key) | ✅ Optional |

> The SLM does **not** play chess. It only drives the personality layer. The minimax engine always plays Black.

---

## Features

- ♟ **Full chess rules** — legal move highlighting, check/checkmate detection, SAN history
- 🤖 **Minimax AI** with alpha-beta pruning — a real opponent, not random moves
- 💬 **Rex** — an SLM-powered rival with a humble-arrogant personality and 50+ non-repeating quips
- 💡 **Press `H`** on your turn for a Gemini-powered coaching hint on the current position
- 🎨 **Dark theme UI** — chess.com-style board colours, last-move highlights, green selection
- 🔄 **New game** resets everything without a page reload

---

## Architecture

```
Browser click
    │
    ▼
Flask /api/move          ← validates UCI move via python-chess
    │
    ├─► game.py          ← updates board state, returns FEN + SAN
    │
    ├─► slm.py           ← generates Rex trash talk for the event
    │        │
    │        └─► SmolLM2 (local) or fallback line bank
    │
    └─► /api/ai-move     ← minimax picks Black's reply

Press H
    │
    ▼
Flask /api/hint
    │
    └─► llm_hint.py      ← FEN + legal moves → Gemini Flash Lite → coaching text
```

---

## Choosing Your Local Model

Edit **two constants** at the top of `slm.py` — nothing else needs changing.

```python
# slm.py — top of file
MODEL_ID     = 'HuggingFaceTB/SmolLM2-135M-Instruct'  # ← change this
LOCAL_FOLDER = 'smollm2-135m-instruct'                 # ← and this
```

| Model | Disk | Speed (CPU) | Quality | Best for |
|---|---|---|---|---|
| `SmolLM2-135M-Instruct` | ~280 MB | ~1200 tok/s | Weak — falls back to curated lines | Low-RAM / quick testing |
| `SmolLM2-360M-Instruct` ✅ | ~720 MB | ~600 tok/s | Noticeably better coherence | **Most users — recommended** |
| `SmolLM2-1.7B-Instruct` | ~3.4 GB | ~150 tok/s | Good conversation quality | 16 GB+ RAM |

> **Fallback guarantee** — if the model isn't downloaded or produces garbage output, Rex automatically uses the hand-crafted line bank. The experience never breaks.

### Swap steps

```bash
# 1. Edit slm.py — update MODEL_ID and LOCAL_FOLDER

# 2. Re-download
python scripts/download_model.py

# 3. Restart
python app.py
```

**Copy-paste values:**

```python
# 360M — recommended
MODEL_ID     = 'HuggingFaceTB/SmolLM2-360M-Instruct'
LOCAL_FOLDER = 'smollm2-360m-instruct'

# 1.7B — best quality
MODEL_ID     = 'HuggingFaceTB/SmolLM2-1.7B-Instruct'
LOCAL_FOLDER = 'smollm2-1.7b-instruct'
```

---

## Rex — the AI Rival

Rex is not your assistant. He's your opponent with opinions.

| Trait | What it looks like |
|---|---|
| **Humble** | Genuinely acknowledges good moves |
| **Arrogant** | Absolutely certain he will win regardless |
| **Dry humour** | One-liners, not rambling |
| **Non-repeating** | Tracks last used line per event category, never fires the same quip twice in a row |
| **Never toxic** | Chess confidence only — no personal attacks |

**Example lines:**

```
"Solid move. Genuinely. Now watch me dismantle it anyway."
"Your pawn structure has the aesthetic of a Tuesday morning."
"I admit defeat. I also reserve the right to rematch immediately."
"You took material. I'm taking the initiative. Fair trade?"
"One of us has a plan. The other has pieces in random squares."
```

---

## Project Structure

```
chess-ai-slm/
├── app.py                  # Flask app — routes and REST API
├── game.py                 # python-chess board + minimax AI (Black)
├── slm.py                  # SmolLM2 wrapper — Rex persona + fallback bank
├── llm_hint.py             # Gemini Flash Lite hint call
├── requirements.txt
├── scripts/
│   └── download_model.py   # One-time model download
├── templates/
│   └── index.html          # Jinja2 UI template
├── static/
│   ├── app.js              # Board interaction, H key, chat
│   └── style.css           # Dark theme, chess.com-style board
└── models/                 # Auto-created by download_model.py
```

---

## Setup

```bash
git clone https://github.com/sharvinvarghese/chess-ai-slm
cd chess-ai-slm

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# One-time model download
# Default: 135M (~280 MB). Edit slm.py first to pick a different size.
python scripts/download_model.py

python app.py
```

Open **http://127.0.0.1:5000**

---

## Using Hints (H key)

1. It must be **your turn** (White).
2. Paste a [Gemini API key](https://aistudio.google.com/app/apikey) into the hint box, **or** set the env var:
   ```bash
   export GEMINI_API_KEY=your_key_here
   ```
3. Press **`H`** anywhere on the page (not while typing in a field).
4. The current FEN + legal moves are sent to **Gemini Flash Lite**.
5. Coaching text appears in the hint panel.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/state` | Board state — FEN, legal moves, SAN history, check/mate flags |
| `POST` | `/api/move` | Submit player move (UCI format, e.g. `e2e4`) |
| `POST` | `/api/ai-move` | Trigger minimax move for Black |
| `POST` | `/api/chat` | Send message to Rex, get SLM reply |
| `POST` | `/api/trash-talk` | Request event-based Rex quip (`move`, `check`, `capture`, `win`, `loss`) |
| `POST` | `/api/hint` | Get Gemini coaching hint for current position |
| `POST` | `/api/new-game` | Reset board |
| `GET` | `/api/model-status` | Check if local SLM is loaded and ready |

---

## Contributing

PRs welcome. Good areas to contribute:

- **Stockfish integration** — swap minimax for `chess.engine.SimpleEngine`
- **Streaming chat** — Server-Sent Events for Rex's replies
- **Stronger evaluation** — piece-square tables, mobility scoring
- **Board themes** — additional colour schemes
- **Opening book** — ECO-based first moves for the AI

Open an issue first for anything larger than a bugfix.
