import pygame
import chess
import chess.pgn
import time
import os
import datetime

# Initialize pygame
pygame.init()

# Display settings
WIDTH, HEIGHT = 800, 640
BOARD_SIZE = 640
SQUARE_SIZE = BOARD_SIZE // 8
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dark Chess")

# Colors
LIGHT_BROWN = (240, 217, 181)
DARK_BROWN = (181, 136, 99)
SELECTED = (150, 150, 50)
HIGHLIGHT = (200, 200, 100)
MOVE_HISTORY_TEXT_COLOR = (255, 255, 255)

# Load placeholder "piece images" as font-rendered text
pieces_img = {}
PIECE_NAMES = ['P','N','B','R','Q','K','p','n','b','r','q','k']
for piece in PIECE_NAMES:
    pieces_img[piece] = pygame.font.SysFont(None, 72).render(piece, True, (0, 0, 0))  # Initial color, not used directly

# Game state
board = chess.Board()
selected_square = None
legal_moves = []
game_moves = []
move_times = []

# Timing
start_time = None
white_time = 600  # 10 minutes
black_time = 600
player_turn_start = None
competitive_mode = False
move_history_font = pygame.font.SysFont(None, 24)

# Game mode
game_mode = None

def draw_board():
    colors = [LIGHT_BROWN, DARK_BROWN]
    for rank in range(8):
        for file in range(8):
            color = colors[(rank + file) % 2]
            rect = pygame.Rect(file*SQUARE_SIZE, rank*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(screen, color, rect)

    if selected_square is not None:
        file, rank = selected_square
        pygame.draw.rect(screen, SELECTED, pygame.Rect(file*SQUARE_SIZE, rank*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        for move in legal_moves:
            x = chess.square_file(move.to_square)
            y = 7 - chess.square_rank(move.to_square)
            pygame.draw.circle(screen, HIGHLIGHT, (x*SQUARE_SIZE + SQUARE_SIZE//2, y*SQUARE_SIZE + SQUARE_SIZE//2), 10)

def draw_pieces():
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            file = chess.square_file(square)
            rank = 7 - chess.square_rank(square)
            symbol = piece.symbol()
            piece_color = (255, 255, 255) if piece.color == chess.WHITE else (0, 0, 0)
            piece_img = pygame.font.SysFont(None, 72).render(symbol, True, piece_color)
            screen.blit(piece_img, (file*SQUARE_SIZE + 18, rank*SQUARE_SIZE + 8))

def get_square_under_mouse():
    mx, my = pygame.mouse.get_pos()
    if mx < BOARD_SIZE:
        return mx // SQUARE_SIZE, my // SQUARE_SIZE
    return None

def square_to_index(file, rank):
    return chess.square(file, 7 - rank)

def draw_timers():
    font = pygame.font.SysFont(None, 36)
    timer_text_color = (255, 255, 255)
    if competitive_mode:
        wt = format_time(white_time)
        bt = format_time(black_time)
        screen.blit(font.render(f"White: {wt}", True, timer_text_color), (660, 50))
        screen.blit(font.render(f"Black: {bt}", True, timer_text_color), (660, 100))

def format_time(seconds):
    minutes = int(seconds // 60)
    sec = int(seconds % 60)
    return f"{minutes:02}:{sec:02}"

def draw_move_history():
    y = 180
    for idx, (move, secs) in enumerate(zip(game_moves, move_times)):
        txt = f"{idx+1}. {move.uci()} ({secs:.1f}s)"
        surface = move_history_font.render(txt, True, MOVE_HISTORY_TEXT_COLOR)
        screen.blit(surface, (660, y))
        y += 20

def reset_game():
    global board, selected_square, legal_moves, game_moves, move_times
    board = chess.Board()
    selected_square = None
    legal_moves = []
    game_moves = []
    move_times = []

def save_pgn():
    game = chess.pgn.Game()
    node = game
    for move in game_moves:
        node = node.add_variation(move)
    filename = datetime.datetime.now().strftime("game_history_%Y%m%d_%H%M%S.pgn")
    with open(filename, "w") as f:
        print(game, file=f)

def handle_player_move():
    global selected_square, legal_moves, player_turn_start, white_time, black_time

    square_clicked = get_square_under_mouse()
    if square_clicked is None:
        return

    file, rank = square_clicked
    clicked_index = square_to_index(file, rank)

    if board.piece_at(clicked_index) and board.color_at(clicked_index) == board.turn:
        selected_square = (file, rank)
        legal_moves.clear()
        for move in board.legal_moves:
            if move.from_square == clicked_index:
                legal_moves.append(move)
    elif selected_square is not None:
        from_sq = square_to_index(*selected_square)
        move = chess.Move(from_sq, clicked_index)
        if move in board.legal_moves:
            move_duration = time.time() - player_turn_start if player_turn_start else 0
            game_moves.append(move)
            move_times.append(move_duration)
            board.push(move)

            if competitive_mode:
                if board.turn == chess.WHITE:
                    black_time -= move_duration
                else:
                    white_time -= move_duration

            selected_square = None
            legal_moves.clear()
            player_turn_start = time.time()

def show_mode_selector():
    global game_mode, competitive_mode
    font = pygame.font.SysFont(None, 42)
    selector_text_color = (255, 255, 255)
    button_text_color = (0, 0, 0)
    button_color = (60, 60, 60)
    running = True
    while running:
        screen.fill(DARK_BROWN)
        title = font.render("Select Game Mode", True, selector_text_color)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))

        modes = ["Friendly PvP", "Competitive PvP", "Quit"]
        for i, label in enumerate(modes):
            rect = pygame.Rect(WIDTH//2 - 140, 200 + i*80, 280, 60)
            pygame.draw.rect(screen, button_color, rect)
            text = font.render(label, True, button_text_color)
            screen.blit(text, (rect.x + 20, rect.y + 10))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if 200 <= my < 260:
                    game_mode = "friendly"
                    competitive_mode = False
                    running = False
                elif 280 <= my < 340:
                    game_mode = "competitive"
                    competitive_mode = True
                    running = False
                elif 360 <= my < 420:
                    pygame.quit()
                    return "quit"

    return game_mode

def main():
    global player_turn_start, white_time, black_time
    clock = pygame.time.Clock()
    mode = show_mode_selector()
    if mode == "quit":
        return
    reset_game()
    player_turn_start = time.time()

    running = True
    while running:
        screen.fill(DARK_BROWN)
        draw_board()
        draw_pieces()
        draw_timers()
        draw_move_history()

        pygame.display.flip()

        if competitive_mode:
            now = time.time()
            elapsed = now - player_turn_start
            if board.turn == chess.WHITE:
                display_time = max(0, white_time - elapsed)
            else:
                display_time = max(0, black_time - elapsed)

            if display_time <= 0:
                print("Time’s up!")
                running = False

        if board.is_game_over():
            print("Game Over:", board.result())
            running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                save_pgn()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_player_move()

        clock.tick(60)

    pygame.quit()

def save_game_summary():
    if not game_moves:
        return

    if not os.path.exists("game_logs"):
        os.makedirs("game_logs")

    filename = datetime.datetime.now().strftime("game_logs/move_log_%Y%m%d_%H%M%S.txt")
    with open(filename, "w") as f:
        for i, (move, t) in enumerate(zip(game_moves, move_times)):
            line = f"{i+1}. {move.uci()} - {t:.2f} sec\n"
            f.write(line)

    print(f"Game log saved to {filename}")

if __name__ == "__main__":
    main()
    save_game_summary()
