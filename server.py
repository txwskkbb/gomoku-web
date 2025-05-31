from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

BOARD_SIZE = 20
WIN_COUNT = 5
MAX_DEPTH = 2
EMPTY, PLAYER, AI = 0, 1, 2
directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
game_over = False

def reset_game():
    global board, game_over
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    game_over = False

def check_win(row, col, player):
    for dr, dc in directions:
        count = 1
        for d in [1, -1]:
            r, c = row, col
            for _ in range(WIN_COUNT):
                r += dr * d
                c += dc * d
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
                    count += 1
                else:
                    break
        if count >= WIN_COUNT:
            return True
    return False

def evaluate_board(board, player):
    score = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                p = board[r][c]
                if p == player:
                    score += evaluate_point(board, r, c, p)
                else:
                    score -= 0.8 * evaluate_point(board, r, c, p)
    return score

def evaluate_point(board, row, col, player):
    score = 0
    for dr, dc in directions:
        line = []
        for i in range(-4, 5):
            r, c = row + dr * i, col + dc * i
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                line.append(board[r][c])
            else:
                line.append(-1)
        patterns = [
            ([player]*5, 10000),
            ([EMPTY, player, player, player, player, EMPTY], 5000),
            ([EMPTY, player, player, player, EMPTY], 500),
            ([EMPTY, player, player, EMPTY], 50),
            ([player, player, player, player, EMPTY], 1000),
            ([EMPTY, player, player, player, player], 1000),
            ([player, player, player, EMPTY, EMPTY], 50),
            ([EMPTY, EMPTY, player, player, player], 50),
        ]
        for pattern, val in patterns:
            for i in range(len(line) - len(pattern) + 1):
                if line[i:i+len(pattern)] == pattern:
                    score += val
    return score

def generate_candidates():
    candidates = set()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                            candidates.add((nr, nc))
    return candidates if candidates else [(BOARD_SIZE // 2, BOARD_SIZE // 2)]

def minimax(board, depth, is_maximizing, alpha, beta):
    score = evaluate_board(board, AI)
    if abs(score) >= 10000 or depth == 0:
        return score
    candidates = generate_candidates()
    if is_maximizing:
        max_eval = float('-inf')
        for row, col in candidates:
            board[row][col] = AI
            eval = minimax(board, depth - 1, False, alpha, beta)
            board[row][col] = EMPTY
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for row, col in candidates:
            board[row][col] = PLAYER
            eval = minimax(board, depth - 1, True, alpha, beta)
            board[row][col] = EMPTY
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def ai_move():
    best_score = float('-inf')
    move = None
    for row, col in generate_candidates():
        board[row][col] = AI
        score = minimax(board, MAX_DEPTH, False, float('-inf'), float('inf'))
        board[row][col] = EMPTY
        if score > best_score:
            best_score = score
            move = (row, col)
    return move

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/new_game", methods=["POST"])
def new_game():
    reset_game()
    return jsonify({"status": "ok"})

@app.route("/player_move", methods=["POST"])
def player_move():
    global board, game_over
    if game_over:
        return jsonify({"status": "error", "message": "游戏已结束"})
    data = request.get_json()
    row, col = data["row"], data["col"]
    if board[row][col] != EMPTY:
        return jsonify({"status": "error", "message": "该位置已有棋子"})
    board[row][col] = PLAYER
    if check_win(row, col, PLAYER):
        game_over = True
        return jsonify({"status": "ok", "message": "你赢了！"})
    move = ai_move()
    if move:
        r, c = move
        board[r][c] = AI
        if check_win(r, c, AI):
            game_over = True
            return jsonify({"status": "ok", "ai_move": move, "message": "AI 赢了！"})
        return jsonify({"status": "ok", "ai_move": move})
    else:
        return jsonify({"status": "ok", "message": "平局"})

if __name__ == "__main__":
    app.run(debug=True)
