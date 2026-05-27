# ♟ Chess AI — SLM + LLM Hints

A fully-featured browser chess game with:

- **Minimax chess engine** (depth 1-4, adjustable difficulty)
- **SLM AI opponent chat** — the AI trash-talks and comments on your moves using Gemini Flash Lite
- **LLM Hint System** — press `H` (or any custom key) to send the current FEN to Gemini for a grandmaster-level explanation of the best move
- **Real-time chat** — type anything and the AI responds in-character using Gemini
- **Full chess rules** — castling, en passant, promotion, check/checkmate/stalemate detection

## How to Use

1. Open `chess-ai-slm.html` in any browser
2. Go to **⚙ CONFIG** tab and paste your [Gemini API key](https://aistudio.google.com)
3. Play as **White** — click a piece then click the destination
4. Press **H** at any time on your turn for an LLM hint
5. Chat with the AI in the 💬 CHAT tab

## Keys
| Key | Action |
|-----|--------|
| `H` | Request Gemini hint for current position |
| Custom | Set any key in Config tab |

## Architecture

```
Chess Engine (pure JS minimax + alpha-beta)
    ↓
Game State → FEN → Gemini Flash Lite API
    ↑                      ↓
AI Opponent Chat ←── SLM response
    ↑
Hint System (LLM call with FEN + prompt)
```

## Without API Key
- Chess engine still plays (full minimax AI)
- Chat uses pre-built persona responses
- Hints fall back to engine suggestion

## Tech
- Vanilla JS, HTML5, CSS3 — no dependencies
- Gemini 2.0 Flash Lite as the SLM backend
- Minimax with alpha-beta pruning + positional tables
