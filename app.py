import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from game import ChessGame
from slm import TrashTalkSLM
from llm_hint import request_hint

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, template_folder='templates', static_folder='static')

game = ChessGame()
slm = TrashTalkSLM(model_dir=BASE_DIR / 'models')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/state', methods=['GET'])
def state():
    return jsonify(game.state_payload())


@app.route('/api/new-game', methods=['POST'])
def new_game():
    game.reset()
    return jsonify({
        'ok': True,
        'state': game.state_payload(),
        'message': 'New game started.'
    })


@app.route('/api/move', methods=['POST'])
def move():
    data = request.get_json(force=True)
    move_uci = data.get('move', '').strip()
    result = game.player_move(move_uci)
    if not result['ok']:
        return jsonify(result), 400
    return jsonify(result)


@app.route('/api/ai-move', methods=['POST'])
def ai_move():
    result = game.ai_move()
    return jsonify(result)


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(force=True)
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'ok': False, 'error': 'Empty message'}), 400
    reply = slm.reply_to_chat(
        user_message=message,
        fen=game.board.fen(),
        move_stack=[m.uci() for m in game.board.move_stack],
        side_to_move='white' if game.board.turn else 'black',
    )
    return jsonify({'ok': True, 'reply': reply, 'model_ready': slm.is_ready()})


@app.route('/api/trash-talk', methods=['POST'])
def trash_talk():
    data = request.get_json(force=True)
    event = data.get('event', 'move')
    reply = slm.generate_trash_talk(
        event=event,
        fen=game.board.fen(),
        move_stack=[m.uci() for m in game.board.move_stack],
        side_to_move='white' if game.board.turn else 'black',
    )
    return jsonify({'ok': True, 'reply': reply, 'model_ready': slm.is_ready()})


@app.route('/api/hint', methods=['POST'])
def hint():
    data = request.get_json(force=True)
    api_key = data.get('api_key', '').strip() or os.getenv('GEMINI_API_KEY', '').strip()
    if not api_key:
        return jsonify({
            'ok': False,
            'error': 'Missing API key. Add it in Settings or set GEMINI_API_KEY env var.'
        }), 400
    result = request_hint(
        api_key=api_key,
        fen=game.board.fen(),
        legal_moves=[m.uci() for m in game.board.legal_moves],
        side_to_move='white' if game.board.turn else 'black'
    )
    return jsonify(result)


@app.route('/api/model-status', methods=['GET'])
def model_status():
    return jsonify(slm.status())


if __name__ == '__main__':
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    app.run(host=host, port=port, debug=debug)
