import ast
import random

class Board:
    def __init__(self, filename):
        self.filename = filename
        self.board = []
        self.rows = 0
        self.cols = 0
        self.num_mines = 0
        # state trackers
        self.revealed = set()
        self.flagged = set()
        self.load_board()

    def load_board(self):
        with open(self.filename, 'r') as f:
            header = f.readline().strip().split()
            if len(header) != 3:
                raise ValueError("First line must be: rows cols num_mines")
            self.rows, self.cols, self.num_mines = map(int, header)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) != self.cols:
                    raise ValueError(f"Expected {self.cols} columns per row, got {len(parts)}")
                row = [('*' if val == '*' else int(val)) for val in parts]
                self.board.append(row)
            if len(self.board) != self.rows:
                raise ValueError(f"Expected {self.rows} rows, got {len(self.board)}")

    def print_board(self, reveal_all=False):
        # Display column indices
        print("Current Board State:")
        # Header: column numbers
        header = '   ' + ' '.join(f"{c:>2}" for c in range(self.cols))
        print(header)
        for r in range(self.rows):
            row_repr = []
            for c in range(self.cols):
                if reveal_all or (r, c) in self.revealed:
                    cell_str = str(self.board[r][c]).rjust(2)
                elif (r, c) in self.flagged:
                    cell_str = 'F'.rjust(2)
                else:
                    cell_str = '?'.rjust(2)
                row_repr.append(cell_str)
            # Prefix row index
            print(str(r).rjust(2) + ' ' + ' '.join(row_repr))

    def reveal(self, r, c):
        if (r, c) in self.revealed or (r, c) in self.flagged:
            return None
        self.revealed.add((r, c))
        return self.board[r][c]

    def flag(self, r, c):
        if (r, c) not in self.revealed:
            self.flagged.add((r, c))

    def unflag(self, r, c):
        self.flagged.discard((r, c))

    def is_mine(self, r, c):
        return self.board[r][c] == '*'

    def get_neighbors(self, r, c):
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),           (0, 1),
                      (1, -1),  (1, 0),  (1, 1)]
        neighbors = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                neighbors.append((nr, nc))
        return neighbors

    def apply_move(self, action, coords):
        r, c = coords
        if action == 'F':
            self.flag(r, c)
            return 'flagged'
        elif action == 'U':
            self.unflag(r, c)
            return 'unflagged'
        elif action == 'R':
            if (r, c) in self.flagged:
                return 'flagged_cell'
            result = self.reveal(r, c)
            if result is None:
                return 'already_revealed'
            if result == '*':
                return 'hit_mine'
            return result
        else:
            return 'invalid_action'

    def is_solved(self):
        total_cells = self.rows * self.cols
        return len(self.revealed) == total_cells - self.num_mines


def interactive_loop(board):
    """
    Run an interactive Minesweeper session on the given Board.
    """
    while True:
        board.print_board()
        move_input = input("Enter move (e.g., 'R 3 4' or 'F 4 5'): ")
        tokens = move_input.strip().split()
        if len(tokens) != 3:
            print("Invalid input. Format must be: ACTION row col")
            continue
        action, r_str, c_str = tokens
        action = action.upper()
        try:
            r, c = int(r_str), int(c_str)
        except ValueError:
            print("Row and column must be integers.")
            continue
        if not (0 <= r < board.rows and 0 <= c < board.cols):
            print(f"Coordinates ({r}, {c}) out of bounds. Please enter 0 ≤ row < {board.rows}, 0 ≤ col < {board.cols}.")
            continue

        result = board.apply_move(action, (r, c))
        if result == 'hit_mine':
            board.print_board(reveal_all=True)
            print(f"GAME OVER! You hit a mine at {(r, c)}.")
            break
        elif result == 'already_revealed':
            print(f"Cell {(r, c)} is already revealed.")
        elif result == 'flagged_cell':
            print(f"Cell {(r, c)} is flagged. Unflag before revealing.")
        elif result == 'invalid_action':
            print(f"Invalid action '{action}'. Use 'F', 'U', or 'R'.")
        else:
            print(f"Move result at {(r, c)}: {result}")

        if board.is_solved():
            board.print_board(reveal_all=True)
            print("Congratulations! You cleared all non-mine cells!")
            break


def run(filename):
    """
    Load a board from the given filename, reveal one random safe tile, and start the interactive loop.
    """
    board = Board(filename)
    # reveal one random safe tile
    safe_tiles = [(r, c) for r in range(board.rows)
                  for c in range(board.cols)
                  if not board.is_mine(r, c) and board.board[r][c] == 0]
    if safe_tiles:
        first = random.choice(safe_tiles)
        board.reveal(*first)
        print(f"First move: revealed a safe tile at {first}.")
    interactive_loop(board)

if __name__ == '__main__':
    fname = input("Enter board filename: ")
    run(fname)
