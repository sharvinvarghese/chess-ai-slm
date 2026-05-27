# ♟ Chess AI SLM

A complete **Flask** chess web app built with:

- **[python-chess](https://python-chess.readthedocs.io/en/latest/core.html)** for move generation, legality, FEN, SAN history, and game-over detection
- **Local SLM** (SmolLM2 family) for trash talk and in-game chat as **Rex** — a chess rival who is simultaneously humble and arrogant
- **[Flask](https://flask.palletsprojects.com/en/stable/quickstart/)** for routing, templates, and REST API endpoints
- **Gemini Flash Lite** (cloud, API key required) for on-demand coaching hints via the `H` key

---

## Features

| Feature | Detail |
|---|---|
| Chess engine | `python-chess` — fully legal move generation |
| AI opponent | Python minimax with alpha-beta pruning (Black side) |
| Local SLM | SmolLM2 family for trash talk + chat as Rex |
| Rex persona | Humble-arrogant, dry wit, non-repeating humour |
| H key hint | Current FEN sent to Gemini Flash Lite for coaching |
| New game | Reset board and state via button or API |
| Move history | SAN notation logged in the sidebar |
| Check / checkmate | Highlighted in UI with badges |

---

## Choosing Your Local Model

You can swap the local SLM based on your RAM, disk space, and patience. Edit **two lines** in `slm.py`:

```python
# slm.py — top of file
MODEL_ID     = 'HuggingFaceTB/SmolLM2-135M-Instruct'  # ← change this
LOCAL_FOLDER = 'smollm2-135m-instruct'                 # ← and this
```

| Model | Disk | Speed (CPU) | Instruction quality | Recommended for |
|---|---|---|---|---|
| `SmolLM2-135M-Instruct` | ~280 MB | ~1200 tok/s | Weak — mostly uses fallbacks | Low-RAM machines, testing |
| `SmolLM2-360M-Instruct` ✅ | ~720 MB | ~600 tok/s | Noticeably better coherence | **Most users — best balance** |
| `SmolLM2-1.7B-Instruct` | ~3.4 GB | ~150 tok/s | Good conversation quality | 16 GB+ RAM, dedicated machine |

### How to swap

```bash
# 1. Edit slm.py — update MODEL_ID and LOCAL_FOLDER to your chosen model

# 2. Delete old model and re-download
python scripts/download_model.py

# 3. Restart the server
python app.py
```

Example values for each model:

```python
# 360M (recommended)
MODEL_ID     = 'HuggingFaceTB/SmolLM2-360M-Instruct'
LOCAL_FOLDER = 'smollm2-360m-instruct'

# 1.7B (best quality)
MODEL_ID     = 'HuggingFaceTB/SmolLM2-1.7B-Instruct'
LOCAL_FOLDER = 'smollm2-1.7b-instruct'
```

> **Note:** The fallback line bank in `slm.py` always works regardless of model. If the model is not downloaded or produces bad output, Rex will use the hand-crafted fallbacks automatically.

---

## Rex — the Chat Persona

Rex is your chess rival. His personality:
- **Humble when genuinely impressed** — he acknowledges good moves sincerely
- **Arrogant about outcomes** — he is absolutely certain he will win regardless
- **Dry, non-repeating humour** — the bot tracks the last line used per category and avoids repeating it
- **Never toxic** — no personal attacks, just chess confidence

Example Rex lines:
> *"Solid move. Genuinely. Now watch me dismantle it anyway."*
> *"Your pawn structure has the aesthetic of a Tuesday morning."*
> *"I admit defeat. I also reserve the right to rematch immediately."*

---

## Project Structure

```text
chess-ai-slm/
├── app.py                  # Flask app — routes and API
├── game.py                 # python-chess game state + minimax AI
├── slm.py                  # Local SLM wrapper (Rex persona)
├── llm_hint.py             # Gemini hint call using current FEN
├── requirements.txt
├── scripts/
│   └── download_model.py   # First-run SLM download
├── templates/
│   └── index.html          # Jinja2 template
├── static/
│   ├── app.js              # Board interaction + H key + chat
│   └── style.css
└── models/                 # Created by download_model.py
```

---

## Setup

```bash
git clone https://github.com/sharvinvarghese/chess-ai-slm
cd chess-ai-slm
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Download local SLM (one-time)
# Default is 135M (~280 MB). Edit slm.py first if you want 360M or 1.7B.
python scripts/download_model.py

# Run
python app.py
```

Open **http://127.0.0.1:5000**

---

## How the H key works

1. It is your turn (White).
2. Paste your **Gemini API key** in the hint settings box (or set `GEMINI_API_KEY` env var).
3. Press **H** anywhere on the page (not in an input).
4. The frontend calls `/api/hint`.
5. Flask forwards the current FEN + legal moves to Gemini Flash Lite.
6. The coaching response appears in the hint box.

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/state` | Current board state (FEN, legal moves, SAN history) |
| POST | `/api/move` | Submit a player move (UCI format) |
| POST | `/api/ai-move` | Trigger AI move for Black |
| POST | `/api/chat` | Send a message to Rex (SLM) |
| POST | `/api/trash-talk` | Request event-based trash talk from Rex |
| POST | `/api/hint` | Get Gemini hint for current position |
| POST | `/api/new-game` | Reset the board |
| GET | `/api/model-status` | Check if local SLM is loaded |

---

## Contributing

Found a bug or want to add Stockfish support, a stronger evaluator, or streaming chat? Open an issue and raise a PR.
