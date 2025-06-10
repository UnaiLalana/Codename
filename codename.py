import sys
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QMessageBox, QStackedLayout
)
from PySide6.QtCore import Qt


def generate_agent_board():
    board = np.zeros((5, 5))
    indices = np.random.choice(25, 9 + 9 + 1, replace=False)
    board.flat[indices[:9]] = 1  # Blue
    board.flat[indices[9:18]] = 2  # Red
    board.flat[indices[18]] = -1  # Black
    return board


def generate_player_board():
    with open("wordlist.txt", "r", encoding="utf-8") as f:
        words = list(set(f.read().split()))
    if len(words) < 25:
        raise ValueError("wordlist.txt must have at least 25 unique words.")
    chosen = np.random.choice(words, 25, replace=False)
    return chosen.reshape(5, 5)


class Codenames(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Codenames - PySide6")
        self.setMinimumSize(700, 700)

        self.agent_board = generate_agent_board()
        self.word_board = generate_player_board()
        self.revealed = np.zeros((5, 5), dtype=bool)
        self.score_blue = 0
        self.score_red = 0
        self.team = 1  # 1: Blue, 2: Red
        self.guesses_left = 0
        self.game_started = False

        self.layout = QStackedLayout()
        self.setLayout(self.layout)

        self.init_main_ui()
        self.init_guess_selector()

        self.layout.setCurrentWidget(self.main_widget)

    def init_main_ui(self):
        self.main_widget = QWidget()
        layout = QVBoxLayout()

        self.status_label = QLabel("Vista de espía: Haz clic para comenzar")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.status_label)

        self.grid = QGridLayout()
        self.buttons = []
        for i in range(5):
            row = []
            for j in range(5):
                btn = QPushButton("")
                btn.setMinimumSize(100, 80)
                btn.setStyleSheet(self.get_style(self.agent_board[i][j], reveal=True))
                btn.clicked.connect(lambda checked, x=i, y=j: self.handle_click(x, y))
                self.grid.addWidget(btn, i, j)
                row.append(btn)
            self.buttons.append(row)
        layout.addLayout(self.grid)

        self.score_label = QLabel("🔵 0 - 0 🔴")
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.score_label)

        self.main_widget.setLayout(layout)
        self.layout.addWidget(self.main_widget)

    def init_guess_selector(self):
        self.selector_widget = QWidget()
        vbox = QVBoxLayout()

        title = QLabel("Selecciona el número de intentos")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        vbox.addWidget(title)

        grid = QGridLayout()
        for i in range(1, 10):
            btn = QPushButton(str(i))
            btn.setFixedSize(80, 80)
            btn.setStyleSheet("font-size: 20px;")
            btn.clicked.connect(lambda checked, n=i: self.set_guesses(n))
            grid.addWidget(btn, (i - 1) // 3, (i - 1) % 3)
        vbox.addLayout(grid)

        self.selector_widget.setLayout(vbox)
        self.layout.addWidget(self.selector_widget)

    def handle_click(self, x, y):
        if not self.game_started:
            self.start_game()
            return
        self.reveal_word(x, y)

    def start_game(self):
        for i in range(5):
            for j in range(5):
                word = self.word_board[i][j]
                self.buttons[i][j].setText(word)
                self.buttons[i][j].setStyleSheet("font-size: 14px;")

        self.game_started = True
        self.prompt_turn()

    def prompt_turn(self):
        self.layout.setCurrentWidget(self.selector_widget)

    def set_guesses(self, guesses):
        self.guesses_left = guesses
        self.update_status()
        self.layout.setCurrentWidget(self.main_widget)

    def reveal_word(self, x, y):
        if self.revealed[x, y] or self.guesses_left <= 0:
            return

        self.revealed[x, y] = True
        agent = self.agent_board[x, y]
        btn = self.buttons[x][y]
        btn.setEnabled(False)
        btn.setStyleSheet(self.get_style(agent, reveal=True))
        btn.setText(self.word_board[x][y])

        end_turn = False
        if agent == 1:
            if self.team == 1:
                self.score_blue += 1
                self.guesses_left -= 1
            else:
                end_turn = True
        elif agent == 2:
            if self.team == 2:
                self.score_red += 1
                self.guesses_left -= 1
            else:
                end_turn = True
        elif agent == -1:
            QMessageBox.information(self, "Game Over", f"El equipo {'Azul' if self.team == 1 else 'Rojo'} eligió al agente negro.\n¡Fin del juego!")
            self.close()
            return
        else:
            self.guesses_left -= 1
            end_turn = True

        self.update_status()
        self.check_win()

        if self.guesses_left <= 0 or end_turn:
            self.team = 2 if self.team == 1 else 1
            self.prompt_turn()

    def update_status(self):
        self.status_label.setText(f"Turno: {'🔵 Azul' if self.team == 1 else '🔴 Rojo'} - Intentos: {self.guesses_left}")
        self.score_label.setText(f"🔵 {self.score_blue} - {self.score_red} 🔴")

    def check_win(self):
        if self.score_blue >= 9:
            QMessageBox.information(self, "Victoria", "¡El equipo Azul gana!")
            self.close()
        elif self.score_red >= 9:
            QMessageBox.information(self, "Victoria", "¡El equipo Rojo gana!")
            self.close()

    def get_style(self, agent, reveal=False):
        if not reveal:
            return "font-size: 14px;"
        color = {
            1: "blue",
            2: "red",
            -1: "black",
            0: "gray"
        }.get(agent, "lightgray")
        fg = "white" if agent in [1, 2, -1] else "black"
        return f"background-color: {color}; color: {fg}; font-weight: bold; font-size: 14px;"


if __name__ == "__main__":
    from PySide6 import QtGui
    app = QApplication(sys.argv)
    window = Codenames()
    window.show()
    sys.exit(app.exec())
