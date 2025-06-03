import random
import time
import itertools

class Board:
    def __init__(self, filename):
        self.filename = filename
        self.board = []
        self.rows = 0
        self.cols = 0
        self.num_mines = 0
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
                parts = line.strip().split()
                if not parts:
                    continue
                if len(parts) != self.cols:
                    raise ValueError(f"Expected {self.cols} cols, got {len(parts)}")
                row = [('*' if v == '*' else int(v)) for v in parts]
                self.board.append(row)
        if len(self.board) != self.rows:
            raise ValueError(f"Expected {self.rows} rows, got {len(self.board)}")

    def print_board(self, reveal_all=False):
        header = '   ' + ' '.join(f"{c:>2}" for c in range(self.cols))
        print(header)
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                if reveal_all or (r, c) in self.revealed:
                    row.append(str(self.board[r][c]).rjust(2))
                elif (r, c) in self.flagged:
                    row.append('F'.rjust(2))
                else:
                    row.append('?'.rjust(2))
            print(str(r).rjust(2), ' '.join(row))

    def reveal(self, r, c):
        if (r, c) in self.revealed or (r, c) in self.flagged:
            return None
        self.revealed.add((r, c))
        return self.board[r][c]

    def flag(self, r, c):
        if (r, c) not in self.revealed:
            self.flagged.add((r, c))

    def apply_move(self, action, r, c):
        if action == 'R':
            if (r, c) in self.flagged:
                return 'flagged_cell'
            res = self.reveal(r, c)
            if res is None:
                return 'already_revealed'
            if res == '*':
                return 'hit_mine'
            return res
        elif action == 'F':
            self.flag(r, c)
            return 'flagged'
        else:
            return 'invalid'

    def is_solved(self):
        return len(self.revealed) == self.rows * self.cols - self.num_mines

class MinesweeperAgent:
    def __init__(self, state):
        self.state = [row[:] for row in state]
        self.rows = len(state)
        self.cols = len(state[0])

    def neighbors(self, r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    yield nr, nc

    def propagate(self):
        new_safe, new_mines = set(), set()
        for r in range(self.rows):
            for c in range(self.cols):
                v = self.state[r][c]
                if isinstance(v, int) and 0 <= v <= 8:
                    covered, flagged = [], 0
                    for nr, nc in self.neighbors(r, c):
                        if self.state[nr][nc] == 9:
                            covered.append((nr, nc))
                        elif self.state[nr][nc] == 10:
                            flagged += 1
                    rem = v - flagged
                    if rem == 0 and covered:
                        new_safe.update(covered)
                    if rem == len(covered) and rem > 0:
                        new_mines.update(covered)
        for (r, c) in new_safe:
            if self.state[r][c] == 9:
                self.state[r][c] = 'S'
        for (r, c) in new_mines:
            if self.state[r][c] == 9:
                self.state[r][c] = 10
        return new_safe, new_mines

    def get_forced_actions(self):
        actions = []
        while True:
            safe, mines = self.propagate()
            if not safe and not mines:
                break
            for c in mines:
                actions.append(('F', c[0], c[1], 'forced'))
            for c in safe:
                actions.append(('R', c[0], c[1], 'forced'))
        return actions

    def estimate_probabilities(self):
        constraints, frontier = [], set()
        for r in range(self.rows):
            for c in range(self.cols):
                v = self.state[r][c]
                if isinstance(v, int) and 0 <= v <= 8:
                    covered, flagged = [], 0
                    for nr, nc in self.neighbors(r, c):
                        if self.state[nr][nc] == 9:
                            covered.append((nr, nc))
                        elif self.state[nr][nc] == 10:
                            flagged += 1
                    if covered:
                        frontier.update(covered)
                        constraints.append((covered, v - flagged))
        frontier = list(frontier)
        n = len(frontier)
        if n > 20:
            raise NotImplementedError
        counts = {cell: 0 for cell in frontier}
        total = 0
        for bits in itertools.product([0, 1], repeat=n):
            assign = dict(zip(frontier, bits))
            if all(sum(assign[cell] for cell in cells) == req for cells, req in constraints):
                total += 1
                for cell, val in assign.items():
                    counts[cell] += val
        return {cell: (counts[cell] / total if total else 0) for cell in frontier}

    def next_move(self):
        # 1) forced moves
        forced = self.get_forced_actions()
        if forced:
            return forced
        # 2) probability-based with random tie-break
        try:
            probs = self.estimate_probabilities()
        except NotImplementedError:
            probs = {}
        # certain flags
        for cell, p in probs.items():
            if p == 1.0:
                return [('F', cell[0], cell[1], f'prob={p:.2f}')]
        if probs:
            # pick all with minimal probability
            min_p = min(probs.values())
            best_cells = [cell for cell, p in probs.items() if p == min_p]
            choice = random.choice(best_cells)
            return [('R', choice[0], choice[1], f'prob={min_p:.2f} (tie-break)')]
        # 3) fallback random
        covered = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.state[r][c] == 9]
        if covered:
            choice = random.choice(covered)
            return [('R', choice[0], choice[1], 'random_guess')]
        return []

def get_csp_state(board):
    state = []
    for r in range(board.rows):
        row = []
        for c in range(board.cols):
            if (r, c) in board.flagged:
                row.append(10)
            elif (r, c) in board.revealed:
                v = board.board[r][c]
                row.append(v if isinstance(v, int) else 9)
            else:
                row.append(9)
        state.append(row)
    return state

def solve_ai(board):
    move_count = 0
    print("AI solving...\n")
    while not board.is_solved():
        actions = MinesweeperAgent(get_csp_state(board)).next_move()
        if not actions:
            print("No moves available, stopping.\n")
            break
        for act, r, c, reason in actions:
            move_count += 1
            print(f"=== AI Move {move_count} ===")
            print(f"Action: {act} at ({r}, {c}),  Reason: {reason}")
            res = board.apply_move(act, r, c)
            print(f"Result: {res}\n")
            print("Board after move:")
            board.print_board()
            print()
            # time.sleep(1)
            if res == 'hit_mine':
                print("AI hit a mine. Game over.\n")
                print(f"Total moves: {move_count}\n")
                return
    if board.is_solved():
        print("AI solved the board!\n")
        print(f"Total moves: {move_count}\n")

def manual_loop(board):
    while True:
        board.print_board()
        inp = input("Enter move ('R row col' or 'F row col'): ").split()
        if len(inp) != 3:
            print("Invalid input.\n")
            continue
        act, r, c = inp[0].upper(), int(inp[1]), int(inp[2])
        print(f"You chose: {act} at ({r}, {c})\n")
        res = board.apply_move(act, r, c)
        print(f"Result: {res}\n")
        if res == 'hit_mine':
            print("You hit a mine. Game over.\n")
            return
        if board.is_solved():
            print("You solved the board!\n")
            return

if __name__ == '__main__':
    fn = input("Enter board filename: ")
    b = Board(fn)
    mode = input("Choose mode: (M)anual or (A)I solve: ").strip().upper()
    if mode == 'M':
        manual_loop(b)
    elif mode == 'A':
        solve_ai(b)
    else:
        print("Unknown mode.\n")
