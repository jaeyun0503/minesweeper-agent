import os
from system import Board, solve_ai

NUM_RUNS = 100
MAP_DIR = ""
BASE_FILENAME = "8x8_10mines_map"

win_count = 0

for i in range(1, NUM_RUNS + 1):
    filename = os.path.join(MAP_DIR, f"{BASE_FILENAME}{i}.txt")
    print(f"Running simulation on: {filename}")
    board = Board(filename)
    try:
        solve_ai(board)
        if board.is_solved():
            win_count += 1
    except Exception as e:
        print(f"Error in game {i}: {e}")

print(f"Total wins out of {NUM_RUNS}: {win_count}")
print(f"Win rate: {win_count / NUM_RUNS * 100:.2f}%")
