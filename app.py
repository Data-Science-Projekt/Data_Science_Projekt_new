import subprocess
import sys

from flask import Flask, render_template

app = Flask(__name__)

# Start Streamlit apps as background processes
streamlit_processes = {}


def start_streamlit(script, port):
    if script not in streamlit_processes or streamlit_processes[script].poll() is not None:
        streamlit_processes[script] = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", script,
             "--server.port", str(port),
             "--server.headless", "true",
             "--browser.gatherUsageStats", "false"],
        )

start_streamlit("return_analysis.py", 8501)
start_streamlit("range_analysis.py", 8502)
start_streamlit("marktphasen.py", 8503)
start_streamlit("marktstruktur.py", 8504)
start_streamlit("technische_analyse.py", 8505)
start_streamlit("risikomanagement.py", 8506)

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/daten-methodik")
def daten_methodik():
    return render_template("daten_methodik.html")


@app.route("/renditeanalyse")
def renditeanalyse():
    return render_template("renditeanalyse.html")


@app.route("/volatilitaet")
def volatilitaet():
    return render_template("volatilitaet.html")


@app.route("/marktstruktur")
def marktstruktur():
    return render_template("marktstruktur.html")


@app.route("/marktphasen")
def marktphasen():
    return render_template("marktphasen.html")


@app.route("/technische-analyse")
def technische_analyse():
    return render_template("technische_analyse.html")


@app.route("/risikomanagement")
def risikomanagement():
    return render_template("risikomanagement.html")


@app.route("/fazit")
def fazit():
    return render_template("fazit.html")


@app.route("/team")
def team():
    return render_template("team.html")


if __name__ == "__main__":
    app.run(debug=True, port=5002)
