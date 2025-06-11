import sys
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QMessageBox, QStackedLayout
)
from PySide6.QtCore import Qt, QTimer
from time import sleep
import qrcode
from PySide6.QtGui import QPixmap, QImage
from io import BytesIO
from PySide6.QtWidgets import QSizePolicy



def generate_agent_board():
    board = np.zeros((5, 5))
    indices = np.random.choice(25, 9 + 9 + 1, replace=False)
    board.flat[indices[:9]] = 1
    board.flat[indices[9:18]] = 2
    board.flat[indices[18]] = -1
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
        self.setWindowTitle("Codenames")
        self.setMinimumSize(700, 700)

        self.agent_board = generate_agent_board()
        self.word_board = generate_player_board()
        self.revealed = np.zeros((5, 5), dtype=bool)
        self.score_blue = 0
        self.score_red = 0
        self.team = 1
        self.guesses_left = 0
        self.game_started = False

        self.layout = QStackedLayout()
        self.setLayout(self.layout)

        self.init_main_ui()
        self.init_guess_selector()

        self.layout.setCurrentWidget(self.main_widget)
        self.start_game()

    
    def generate_agent_qr(self):
        # Salva anche la board in HTML leggibile dagli agenti
        html_content = "<html><head><meta charset='utf-8'><style>td{width:80px;height:80px;text-align:center;font-size:18px;font-weight:bold;}</style></head><body><table border='1' cellspacing='0'>"

        color_map = {
            1: "#007BFF",   # blu
            2: "#DC3545",   # rosso
            -1: "#000000",  # nero
            0: "#CCCCCC"    # grigio per neutrali
        }

        for i in range(5):
            html_content += "<tr>"
            for j in range(5):
                word = self.word_board[i][j]
                agent = self.agent_board[i][j]
                color = color_map.get(agent, "#FFFFFF")
                text_color = "white" if agent in [1, 2, -1] else "black"
                html_content += f"<td style='background-color:{color}; color:{text_color};'>{word}</td>"
            html_content += "</tr>"
        html_content += "</table></body></html>"

        # Salva come file HTML da servire
        with open("agent_board.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        np.save("agent_board.npy", self.agent_board)
        np.save("word_board.npy", self.word_board)

        # QR code che punta alla pagina HTML (tramite Flask presumibilmente)
        import socket
        ip = socket.gethostbyname(socket.gethostname())
        url = f"http://{ip}:5000/"

        qr = qrcode.QRCode(box_size=5, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        qimage = QImage.fromData(buffer.read())
        pixmap = QPixmap.fromImage(qimage)
        return pixmap




    def init_main_ui(self):
        self.main_widget = QWidget()
        layout = QVBoxLayout()

        self.status_label = QLabel("Spymasters: scan QR to view the board")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.status_label)

        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setPixmap(self.generate_agent_qr())
        layout.addWidget(self.qr_label)

        self.score_label = QLabel("🔵 0 - 0 🔴")
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setStyleSheet("font-size: 20px;")
        layout.addWidget(self.score_label)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.buttons = [[None for _ in range(5)] for _ in range(5)]

        for i in range(5):
            for j in range(5):
                btn = QPushButton("")
                btn.setMinimumSize(120, 120)
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                btn.setStyleSheet("font-size: 24px;")

                btn.clicked.connect(lambda checked, x=i, y=j: self.handle_click(x, y))
                self.grid_layout.addWidget(btn, i, j)
                self.buttons[i][j] = btn

        self.grid_widget.setLayout(self.grid_layout)
        layout.addWidget(self.grid_widget)

        self.continue_button = QPushButton("Continue")
        self.continue_button.setStyleSheet("font-size: 16px; padding: 10px;")
        self.continue_button.clicked.connect(self.show_guess_selector)
        layout.addWidget(self.continue_button)

        self.main_widget.setLayout(layout)
        self.layout.addWidget(self.main_widget)



    def init_guess_selector(self):
        self.selector_widget = QWidget()
        vbox = QVBoxLayout()

        title = QLabel("Select the number of guesses")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        vbox.addWidget(title)

        grid = QGridLayout()
        for i in range(1, 10):
            btn = QPushButton(str(i))
            btn.setFixedSize(180, 180)
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
                self.buttons[i][j].setStyleSheet("font-size: 28px;")

        self.game_started = True
        self.prompt_turn()

    def prompt_turn(self):
        self.status_label.setText(f"{'🔵 Blue' if self.team == 1 else '🔴 Red'}: Look at the board")
        self.continue_button.show()
        self.layout.setCurrentWidget(self.main_widget)

    def show_guess_selector(self):
        self.continue_button.hide()
        self.layout.setCurrentWidget(self.selector_widget)

    def set_guesses(self, guesses):
        self.guesses_left = guesses
        self.qr_label.hide()  # Nasconde il QR code una volta che il gioco comincia
        self.update_status()
        self.layout.setCurrentWidget(self.main_widget)




    def reveal_word(self, x, y):
        if self.revealed[x, y] or self.guesses_left <= 0:
            return

        self.revealed[x, y] = True
        agent = self.agent_board[x, y]
        btn = self.buttons[x][y]
        btn.setEnabled(False)
        btn.setStyleSheet(self.get_style(agent))
        btn.setText(self.word_board[x][y])

        end_turn = False
        if agent == 1:
            if self.team == 1:
                self.guesses_left -= 1
            else:
                end_turn = True
            self.score_blue += 1
        elif agent == 2:
            if self.team == 2:
                self.guesses_left -= 1
            else:
                end_turn = True
            self.score_red += 1
        elif agent == -1:
            QTimer.singleShot(500, lambda: QMessageBox.information(self, "Game Over", f"Team {'Blue' if self.team == 1 else 'Red'} chose the black agent.\nGame over!"))
            QTimer.singleShot(1000, self.close)
            return
        else:
            self.guesses_left -= 1
            end_turn = True

        self.update_status()
        self.check_win()

        if self.guesses_left <= 0 or end_turn:
            QTimer.singleShot(500, self.next_turn)

    def next_turn(self):
        self.team = 2 if self.team == 1 else 1
        self.prompt_turn()


    def update_status(self):
        self.status_label.setText(f"Turn: {'🔵 Blue' if self.team == 1 else '🔴 Red'} - Guesses: {self.guesses_left}")
        self.score_label.setText(f"🔵 {self.score_blue} - {self.score_red} 🔴")

    def check_win(self):
        if self.score_blue >= 9:
            QMessageBox.information(self, "Victory", "Team Blue wins!")
            self.close()
        elif self.score_red >= 9:
            QMessageBox.information(self, "Victory", "Team Red wins!")
            self.close()

    def get_style(self, agent):
        color = {
            1: "blue",
            2: "red",
            -1: "black",
            0: "gray"
        }.get(agent, "lightgray")
        fg = "white" if agent in [1, 2, -1] else "black"
        return f"background-color: {color}; color: {fg}; font-weight: bold; font-size: 28px;"


if __name__ == "__main__":
    from PySide6 import QtGui
    app = QApplication(sys.argv)
    window = Codenames()
    window.show()
    sys.exit(app.exec())


