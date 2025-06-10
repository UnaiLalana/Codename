import numpy as np


def generate_agent_board():
    """
    Generates a 5x5 board with 9 blue agents, 9 red agents, and 1 black agent.
    The board is represented as a numpy array.
    """

    agents_board = np.zeros_like(np.empty((5, 5)))
    indices_blue = np.random.choice(agents_board.size, 9, replace=False)
    agents_board.flat[indices_blue] = 1

    remaining_indices = np.flatnonzero(agents_board != 1)
    indices_red = np.random.choice(remaining_indices, 9, replace=False)
    agents_board.flat[indices_red] = 2

    remaining_indices_2 = np.flatnonzero(agents_board == 0)
    indices_black = np.random.choice(remaining_indices_2, 1, replace=False)
    agents_board.flat[indices_black] = -1
    
    return agents_board


def generate_player_board():
    """
    Generates a 5x5 board with random words from the wordlist.
    The board is represented as a numpy array.
    """
    with open('wordlist.txt', 'r', encoding='utf-8') as wordlist_file:
        wordlist_content = wordlist_file.read()
    words = np.array(wordlist_content.split())
    players_board = np.empty_like(np.empty((5, 5)), dtype='<U20')

    for i in range(5):
        for j in range(5):
            word = np.random.choice(words)
            while word in players_board:
                word = np.random.choice(words)
            players_board[i, j] = word
    return players_board

def main():
    """
    Main function to run the game.
    """
    agents_board = generate_agent_board()
    players_board = generate_player_board()
    print(agents_board)
    score_blue = 0
    score_red = 0
    game_finished = False
    team = 1
    while not game_finished:
        print(f"Current team: {'Blue' if team == 1 else 'Red'}")
        number_of_guesses = int(input("Enter the number of guesses allowed: "))
        for guess in range(number_of_guesses):
            x, y = input("Enter coordinates (x y) to reveal a word: ").split()
            x, y = int(x), int(y)
            if agents_board[x, y] == 1:
                print("You revealed a blue agent!")
                score_blue += 1
                if team != 1:
                    break
            elif agents_board[x, y] == 2:
                print("You revealed a red agent!")
                score_red += 1
                if team != 2:
                    break
            elif agents_board[x, y] == -1:
                print("You revealed the black agent! Game over.")
                game_finished = True
                break
            else:
                print("You revealed a neutral word.")
        if not game_finished:
            if score_blue >= 9 or score_red >= 9:
                game_finished = True
                if score_blue >= 9:
                    print("Blue team wins!")
                else:
                    print("Red team wins!")
            team = team % 2 + 1