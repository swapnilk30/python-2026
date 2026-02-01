from flask import Flask, render_template
import plotly.graph_objs as go
import plotly.io as pio

from services.market_data_service import fetch_nifty_ohlc
from indicators.rsi import add_rsi
from config import INDICATOR_CONFIG

app = Flask(__name__)


# ======================
# ROUTES
# ======================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard/index.html")

@app.route("/dashboard/settings")
def settings():
    return render_template("dashboard/settings.html")

# ======================
# RUN
# ======================
if __name__ == "__main__":
    app.run(debug=True)