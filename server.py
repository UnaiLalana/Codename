from flask import Flask, render_template_string
import numpy as np

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Spymaster View</title>
    <style>
        table { border-collapse: collapse; margin: 20px auto; }
        td {
            width: 100px; height: 100px; text-align: center;
            font-size: 20px; font-weight: bold;
            border: 1px solid #000;
        }
        .red { background-color: #dc3545; color: white; }
        .blue { background-color: #007bff; color: white; }
        .black { background-color: black; color: white; }
        .neutral { background-color: gray; color: white; }
    </style>
</head>
<body>
    <h1 style="text-align:center;">Spymaster Board</h1>
    <table>
    {% for row in board %}
        <tr>
        {% for cell in row %}
            <td class="{{ cell[1] }}">{{ cell[0] }}</td>
        {% endfor %}
        </tr>
    {% endfor %}
    </table>
</body>
</html>
"""

@app.route("/")
def show_board():
    try:
        agent_board = np.load("agent_board.npy")
        word_board = np.load("word_board.npy", allow_pickle=True)

        label_map = {1: "blue", 2: "red", -1: "black", 0: "neutral"}
        combined_board = [
            [(word_board[i][j], label_map[int(agent_board[i][j])]) for j in range(5)]
            for i in range(5)
        ]

        return render_template_string(HTML, board=combined_board)
    except Exception as e:
        return f"Error loading board: {e}"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")