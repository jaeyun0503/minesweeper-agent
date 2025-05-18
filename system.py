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

    def print_board(self, reveal_all=False):
        print("Current Board State:")
        for r in range(self.rows):
            row_repr = []
            for c in range(self.cols):
                if (r, c) in self.revealed or reveal_all:
                    cell = self.board[r][c]
                    row_repr.append(str(cell))
                elif (r, c) in self.flagged:
                    row_repr.append('F')
                else:
                    row_repr.append('?')
            print(' '.join(row_repr))

    def reveal(self, r, c):
        """Reveal a cell, Returns value '*' or 0–8"""
        if (r, c) in self.revealed or (r, c) in self.flagged:
            return None
        self.revealed.add((r, c))
        return self.board[r][c]

    def flag(self, r, c):
        """Flag cell as mine"""
        if (r, c) not in self.revealed:
            self.flagged.add((r, c))

    def is_mine(self, r, c): #boolean
        return self.board[r][c] == '*'

    def get_neighbors(self, r, c):
        """Return list of valid neighbor coords"""
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1), (0, 1),
                      (1, -1),  (1, 0),  (1, 1)]
        neighbors = []
        for dx, dy in directions:
            nr, nc = r + dx, c + dy
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                neighbors.append((nr, nc))
        return neighbors

    def is_solved(self):
        """Check if all non-mine tiles are revealed"""
        total_cells = self.rows * self.cols
        return len(self.revealed) == total_cells - self.num_mines
    

