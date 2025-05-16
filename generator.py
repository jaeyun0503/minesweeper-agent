import argparse
import os
import random

class Board:
    def __init__(self, filename):
        self.filename = filename
        self.board = []
        self.rows = 0
        self.cols = 0
        self.num_mines = 0
        #state trackers
        self.revealed = set()
        self.flagged = set()
        self.load_board()

    def load_board(self):
        with open(self.filename, 'r') as f:
            header = f.readline().strip().split()
            self.rows, self.cols, self.num_mines = map(int, header)
            for line in f:
                row = []
                for val in line.strip().split():
                    row.append('*' if val == '*' else int(val))
                self.board.append(row)
    


def generate_board(rows, cols, num_mines):
    max_mines = rows * cols - 1
    num_mines = min(num_mines, max_mines)

    board = [[0 for _ in range(cols)] for _ in range(rows)] # initializes empty board
    mine_positions = set()

    # randomly picks a position for each mine
    while len(mine_positions) < num_mines:
        r = random.randint(0, rows - 1)
        c = random.randint(0, cols - 1)
        mine_positions.add((r, c))

    for r, c in mine_positions:
        board[r][c] = '*'

    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    for r in range(rows):
        for c in range(cols):
            if board[r][c] == '*':
                continue
            count = sum(1 for x, y in directions if (0 <= r + x < rows and 0 <= c + y < cols) and (board[r + x][c + y] == '*')) # checks if neighboring cell is inside board and contains a mine
            board[r][c] = count

    return board

def save_as_file(filename, board, rows, cols, num_mines):
    with open(filename, 'w') as f:
        f.write(f"{rows} {cols} {num_mines}\n")
        for row in board:
            f.write(' '.join(str(cell) for cell in row) + '\n')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rows", nargs="?", type=int, default=8, help="number of rows (default: 8)")
    parser.add_argument("cols", nargs="?", type=int, default=None, help="number of columns (default: same as rows)")
    parser.add_argument("mines", nargs="?", type=int, default=10, help="number of mines (default: 10)")
    parser.add_argument("maps", nargs="?", type=int, default=1, help="number of maps to generate (default: 1)")
    parser.add_argument("--output", "-o", type=str, default=".", help="output directory (default: current folder)")
    args = parser.parse_args()

    rows = args.rows
    cols = args.cols if args.cols is not None else rows
    num_mines = args.mines
    num_maps = args.maps
    output_dir = args.output

    # creates directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    for i in range(1, num_maps + 1):
        board = generate_board(rows, cols, num_mines)
        filename = os.path.join(output_dir, f"{rows}x{cols}_{num_mines}mines_map{i}.txt")
        save_as_file(filename, board, rows, cols, num_mines)
        print(f"saved: {filename}")

if __name__ == "__main__":
    main()
