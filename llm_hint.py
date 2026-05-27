import requests


def request_hint(api_key: str, fen: str, legal_moves: list, side_to_move: str) -> dict:
    """
    Send current board state to Gemini Flash Lite and return a coaching hint.
    Called when the user presses H in the browser.
    """
    prompt = (
        'You are an expert chess coach.\n'
        f'Current board state (FEN): {fen}\n'
        f'Side to move: {side_to_move}\n'
        f'Legal moves available (UCI): {legal_moves[:40]}\n\n'
        'Please:\n'
        '1. Suggest the best move in UCI notation and its SAN equivalent.\n'
        '2. Explain why in 2-3 concise sentences (tactical or strategic reason).\n'
        '3. Mention one key threat from the opponent to watch for.\n'
        'Keep the response practical and concise.'
    )

    url = (
        'https://generativelanguage.googleapis.com/v1beta/models/'
        f'gemini-2.0-flash-lite:generateContent?key={api_key}'
    )
    payload = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0.2, 'maxOutputTokens': 200},
    }

    try:
        resp = requests.post(url, json=payload, timeout=25)
        resp.raise_for_status()
        data = resp.json()
        text = data['candidates'][0]['content']['parts'][0]['text'].strip()
        return {'ok': True, 'hint': text}
    except Exception as exc:
        return {'ok': False, 'error': f'Hint request failed: {exc}'}
