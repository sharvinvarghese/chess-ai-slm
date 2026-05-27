// Chess AI SLM — Flask frontend
// Manages board rendering, move interaction, chat, trash talk, and hint (H key)

const FILES = 'abcdefgh';
let currentState   = null;
let selectedSquare = null;
let highlighted    = [];
let lastMoveSquares = [];   // [fromSq, toSq] for last-move highlight

const boardEl     = document.getElementById('board');
const turnBadge   = document.getElementById('turnBadge');
const checkBadge  = document.getElementById('checkBadge');
const gameBadge   = document.getElementById('gameBadge');
const fenBox      = document.getElementById('fenBox');
const chatLog     = document.getElementById('chatLog');
const chatInput   = document.getElementById('chatInput');
const hintBox     = document.getElementById('hintBox');
const apiKeyInput = document.getElementById('apiKeyInput');
const modelStatus = document.getElementById('modelStatus');
const moveList    = document.getElementById('moveList');

// ─── BOARD RENDERING ──────────────────────────────────────────────────────────

function squareColor(fileIdx, rank) {
  return (fileIdx + rank) % 2 === 0 ? 'light' : 'dark';
}

function boardMap(squares) {
  const m = {};
  for (const sq of squares) m[sq.name] = sq;
  return m;
}

function renderBoard(state) {
  currentState = state;
  const map = boardMap(state.board);
  boardEl.innerHTML = '';

  for (let rank = 8; rank >= 1; rank--) {
    for (let fi = 0; fi < 8; fi++) {
      const name = FILES[fi] + rank;
      const sq   = map[name];
      const colorClass = squareColor(fi, rank);   // 'light' or 'dark'
      const div  = document.createElement('div');
      div.className = `square ${colorClass}`;
      div.dataset.sq = name;

      if (selectedSquare === name)        div.classList.add('selected');
      if (highlighted.includes(name))     div.classList.add(sq?.piece ? 'capture' : 'target');
      if (lastMoveSquares.includes(name)) div.classList.add('last-move');

      // king in check
      if (state.check && sq?.piece === (state.turn === 'white' ? 'K' : 'k')) {
        div.classList.add('in-check');
      }

      // rank label (left edge)
      if (fi === 0) {
        const r = document.createElement('span');
        r.className = 'coord rank';
        r.textContent = rank;
        div.appendChild(r);
      }
      // file label (bottom edge)
      if (rank === 1) {
        const f = document.createElement('span');
        f.className = 'coord file';
        f.textContent = FILES[fi];
        div.appendChild(f);
      }

      // piece
      if (sq?.unicode) {
        const p = document.createElement('span');
        // add white/black class so CSS drop-shadow applies correctly
        p.className = `piece ${sq.color || ''}`;
        p.textContent = sq.unicode;
        div.appendChild(p);
      }

      div.addEventListener('click', () => onSquareClick(name, sq));
      boardEl.appendChild(div);
    }
  }

  // status badges
  turnBadge.textContent = state.turn === 'white' ? '⬜ White to move' : '⬛ AI thinking…';
  turnBadge.className   = `badge ${state.turn === 'white' ? 'badge-active' : 'badge-muted'}`;
  checkBadge.style.display = state.check ? '' : 'none';
  gameBadge.textContent = state.game_over
    ? `Game over — ${state.result || 'finished'}`
    : (state.check ? '⚠ Check' : 'In progress');
  fenBox.value = state.fen;

  // move list
  moveList.innerHTML = '';
  state.san_moves.forEach((san, idx) => {
    if (idx % 2 === 0) {
      const num = document.createElement('span');
      num.className   = 'move-num';
      num.textContent = (idx / 2 + 1) + '.';
      moveList.appendChild(num);
    }
    const cell = document.createElement('span');
    cell.className   = 'move-san';
    cell.textContent = san;
    moveList.appendChild(cell);
  });
  moveList.scrollTop = moveList.scrollHeight;
}

// ─── MOVE INTERACTION ─────────────────────────────────────────────────────────

function legalTargets(fromSq) {
  if (!currentState) return [];
  return currentState.legal_moves
    .filter(m => m.slice(0, 2) === fromSq)
    .map(m => m.slice(2, 4));
}

async function onSquareClick(name, sq) {
  if (!currentState || currentState.game_over) return;
  if (currentState.turn !== 'white') return;

  const isOwnPiece = sq?.color === 'white';

  if (!selectedSquare) {
    if (isOwnPiece) {
      selectedSquare = name;
      highlighted    = legalTargets(name);
      renderBoard(currentState);
    }
    return;
  }

  if (selectedSquare === name) {
    selectedSquare = null; highlighted = [];
    renderBoard(currentState);
    return;
  }

  if (isOwnPiece) {
    selectedSquare = name;
    highlighted    = legalTargets(name);
    renderBoard(currentState);
    return;
  }

  // attempt move — prefer promotion to queen
  const base = selectedSquare + name;
  const move = currentState.legal_moves.find(m => m === base)
            || currentState.legal_moves.find(m => m.startsWith(base));

  selectedSquare = null; highlighted = [];

  if (!move) { renderBoard(currentState); return; }

  const res  = await fetch('/api/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ move })
  });
  const data = await res.json();
  if (!data.ok) { addMsg('ai', data.error || 'Illegal move.'); return; }

  lastMoveSquares = [selectedSquare || base.slice(0,2), name];
  addMsg('user', `You played ${data.player_san}`);
  renderBoard(data.state);

  if (data.state.game_over) {
    addMsg('sys', `Game over — ${data.state.result}`);
    fetchTrashTalk('loss');
    return;
  }

  fetchTrashTalk(data.state.check ? 'check' : 'move');

  // trigger AI move
  const aiRes  = await fetch('/api/ai-move', { method: 'POST' });
  const aiData = await aiRes.json();
  if (aiData.ok) {
    // derive last-move squares from UCI
    const aiUCI = aiData.ai_move || '';
    lastMoveSquares = [aiUCI.slice(0,2), aiUCI.slice(2,4)];
    renderBoard(aiData.state);
    addMsg('ai', `I played ${aiData.ai_san}.`);
    fetchTrashTalk(aiData.state.check ? 'check' : 'move');
    if (aiData.state.game_over) addMsg('sys', `Game over — ${aiData.state.result}`);
  }
}

// ─── CHAT ──────────────────────────────────────────────────────────────────────

function addMsg(role, text) {
  const div = document.createElement('div');
  div.className   = `msg ${role}`;
  div.textContent = text;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

async function fetchTrashTalk(event) {
  const res  = await fetch('/api/trash-talk', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ event })
  });
  const data = await res.json();
  if (data.ok && data.reply) addMsg('ai', data.reply);
}

async function sendChat() {
  const msg = chatInput.value.trim();
  if (!msg) return;
  chatInput.value = '';
  addMsg('user', msg);
  const res  = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: msg })
  });
  const data = await res.json();
  addMsg('ai', data.reply || data.error || 'No reply.');
}

// ─── HINTS (H KEY) ─────────────────────────────────────────────────────────────

async function requestHint() {
  if (!currentState || currentState.turn !== 'white') {
    hintBox.textContent = 'Hints are only available on your turn (white).';
    return;
  }
  hintBox.textContent = '⏳ Requesting hint from Gemini…';
  const res  = await fetch('/api/hint', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKeyInput.value.trim() })
  });
  const data = await res.json();
  hintBox.textContent = data.ok ? data.hint : (data.error || 'Hint failed.');
}

document.addEventListener('keydown', e => {
  if (
    e.key.toLowerCase() === 'h' &&
    !e.ctrlKey && !e.altKey && !e.metaKey &&
    document.activeElement.tagName !== 'INPUT' &&
    document.activeElement.tagName !== 'TEXTAREA'
  ) requestHint();
});

// ─── CONTROLS ─────────────────────────────────────────────────────────────────

document.getElementById('sendChatBtn').addEventListener('click', sendChat);
chatInput.addEventListener('keydown', e => { if (e.key === 'Enter') sendChat(); });
document.getElementById('hintBtn').addEventListener('click', requestHint);
document.getElementById('newGameBtn').addEventListener('click', async () => {
  selectedSquare = null; highlighted = []; lastMoveSquares = [];
  const res  = await fetch('/api/new-game', { method: 'POST' });
  const data = await res.json();
  renderBoard(data.state);
  addMsg('sys', 'New game started.');
  fetchTrashTalk('move');
});

// ─── INIT ──────────────────────────────────────────────────────────────────────

async function init() {
  const res  = await fetch('/api/state');
  const data = await res.json();
  renderBoard(data);
  addMsg('sys', 'Chess AI SLM online. Press H for a hint.');
  fetchTrashTalk('move');

  // model status pill
  const ms = await fetch('/api/model-status');
  const md = await ms.json();
  modelStatus.textContent = md.ready
    ? `✓ ${md.model_id}`
    : `✗ ${md.message}`;
  modelStatus.className = `status-pill ${md.ready ? 'ready' : 'error'}`;
}

init();
