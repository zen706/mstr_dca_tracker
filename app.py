from flask import Flask, request, render_template_string, jsonify
import pandas as pd
import plotly.graph_objects as go
from dca.data_loader import load_data
from dca.calculator import DCA_Calculator
from datetime import datetime
from dateutil.relativedelta import relativedelta
import math

app = Flask(__name__)


@app.route("/graph")
def graph():
    investment_value = request.args.get("investment", "10")
    timeframe_value = request.args.get("timeframe", "week")
    accumulate_years_value = request.args.get("accumulate_period", "5")
    include_btc = request.args.get("include_btc", "off")
    start_date_select = request.args.get("start_date_select")
    custom_date = request.args.get("start_date_custom", "")
    if start_date_select == "custom":
        start_date = custom_date or "2015-01-01"
    elif start_date_select:
        start_date = start_date_select
    else:
        start_date = "2015-01-01"

    try:
        investment = float(investment_value)
        timeframe = timeframe_value.lower()
        acc_val = float(accumulate_years_value) if accumulate_years_value else 0
        if acc_val < 1:
            accumulate_period = int(acc_val * 12)
        else:
            accumulate_period = int(acc_val)

        # MSTR
        historical_data_mstr = load_data("MSTR")
        dca_calculator_mstr = DCA_Calculator(
            investment,
            timeframe,
            historical_data_mstr,
            start_date,
            accumulate_period,
        )
        returns_mstr = dca_calculator_mstr.calculate_returns()
        dates_mstr = [data["date"] for data in returns_mstr]
        values_mstr = [data["value"] for data in returns_mstr]
        cumulative_investment_mstr = investment * len(returns_mstr)
        total_invested = cumulative_investment_mstr
        total_value = values_mstr[-1] if values_mstr else 0
        percent_change = (
            (total_value / total_invested * 100) if total_invested > 0 else 0
        )

        btc_df = load_data("BTC-USD")
        current_btc_usd = btc_df["Close"].iloc[-1]
        mstr_df = load_data("MSTR")
        current_mstr_price = mstr_df["Close"].iloc[-1]
        sat_value_calculated = math.floor((total_value / current_btc_usd) * 10**8)
        mstr_shares_calculated = math.floor(total_value / current_mstr_price)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=dates_mstr,
                y=values_mstr,
                mode="lines+markers",
                name="MSTR",
                hovertemplate="Date: %{x}<br>MSTR Value: $%{y:.2f}<extra></extra>",
            )
        )

        summary_stats_btc = ""
        if include_btc == "on":
            dca_calculator_btc = DCA_Calculator(
                investment,
                timeframe,
                load_data("BTC-USD"),
                start_date,
                accumulate_period,
            )
            returns_btc = dca_calculator_btc.calculate_returns()
            dates_btc = [data["date"] for data in returns_btc]
            values_btc = [data["value"] for data in returns_btc]
            cumulative_investment_btc = investment * len(returns_btc)
            fig.add_trace(
                go.Scatter(
                    x=dates_btc,
                    y=values_btc,
                    mode="lines+markers",
                    name="BTC",
                    hovertemplate="Date: %{x}<br>BTC Value: $%{y:.2f}<extra></extra>",
                )
            )
            total_invested_btc = cumulative_investment_btc
            total_value_btc = values_btc[-1] if values_btc else 0
            percent_change_btc = (
                (total_value_btc / total_invested_btc * 100)
                if total_invested_btc > 0
                else 0
            )
            summary_stats_btc = f"""
      <div class="row justify-content-center mt-4">
        <div class="col-12 col-md-4">
          <div class="card shadow-sm">
            <div class="card-body text-center">
              <h2>${total_invested_btc:.2f}</h2>
              <p>Total Invested (BTC)</p>
            </div>
          </div>
        </div>
        <div class="col-12 col-md-4 mt-3 mt-md-0">
          <div class="card shadow-sm">
            <div class="card-body text-center">
              <h2>${total_value_btc:.2f}</h2>
              <p>Total Value (BTC)</p>
            </div>
          </div>
        </div>
        <div class="col-12 col-md-4 mt-3 mt-md-0">
          <div class="card shadow-sm">
            <div class="card-body text-center">
              <h2>{percent_change_btc:.2f}%</h2>
              <p>Percent Change (BTC)</p>
            </div>
          </div>
        </div>
      </div>
            """
        summary_stats = f"""
      <div class="row justify-content-center mt-4">
        <div class="col-12 col-md-4">
          <div class="card shadow-sm">
            <div class="card-body text-center">
              <h2>${total_invested:.2f}</h2>
              <p>Total Invested (MSTR)</p>
            </div>
          </div>
        </div>
        <div class="col-12 col-md-4 mt-3 mt-md-0">
          <div class="card shadow-sm">
            <div class="card-body text-center">
              <h2>${total_value:.2f}</h2>
              <p>{sat_value_calculated:,} Satoshis, {mstr_shares_calculated} MSTR</p>
              <p>Total Value (MSTR)</p>
            </div>
          </div>
        </div>
        <div class="col-12 col-md-4 mt-3 mt-md-0">
          <div class="card shadow-sm">
            <div class="card-body text-center">
              <h2>{percent_change:.2f}%</h2>
              <p>Percent Change (MSTR)</p>
            </div>
          </div>
        </div>
      </div>
      """
        if include_btc == "on":
            summary_stats = summary_stats + summary_stats_btc

        fig.update_layout(
            title="DCA Investment Returns",
            xaxis_title="Date",
            yaxis_title="Portfolio Value (USD)",
            yaxis_type="log",
        )

        graph_html = fig.to_html(full_html=False, include_plotlyjs=False)
        return jsonify({"summary_stats": summary_stats, "graph_html": graph_html})
    except Exception as e:
        return jsonify(
            {
                "summary_stats": f"<p style='color:red;'>Error: {str(e)}</p>",
                "graph_html": "",
            }
        )


@app.route("/", methods=["GET"])
def index():
    investment_value = request.args.get("investment", "10")
    timeframe_value = request.args.get("timeframe", "week")
    accumulate_years_value = request.args.get("accumulate_period", "5")
    include_btc = request.args.get("include_btc", "off")
    start_date_select = request.args.get("start_date_select")
    custom_date = request.args.get("start_date_custom", "")
    if start_date_select == "custom":
        custom_date_div_style = "display: block;"
    else:
        custom_date_div_style = "display: none;"

    today = datetime.today()
    options = []
    half_year = today - relativedelta(months=6)
    options.append(("6months", half_year.strftime("%Y-%m-%d"), "6 months ago"))
    for i in range(1, 11):
        option_date = today - relativedelta(years=i)
        options.append((f"{i}year", option_date.strftime("%Y-%m-%d"), f"{i} year ago"))

    options_html = ""
    for value, date_str, label in options:
        selected = " selected" if start_date_select == date_str else ""
        options_html += f'<option value="{date_str}"{selected}>{label}</option>'
    custom_selected = " selected" if start_date_select == "custom" else ""
    options_html += f'<option value="custom"{custom_selected}>Custom Date</option>'

    form_html = f"""
    <form id="dca-form" autocomplete="off">
      <div class="mb-3">
        <label class="form-label">Investment Amount</label>
        <div class="input-group">
          <span class="input-group-text">$</span>
          <input type="number" name="investment" value="{investment_value}" class="form-control" step="1" min="1">
        </div>
      </div>
      <div class="mb-3">
        <label class="form-label">Timeframe</label>
        <select name="timeframe" class="form-select">
          <option value="day" {"selected" if timeframe_value=="day" else ""}>day</option>
          <option value="week" {"selected" if timeframe_value=="week" else ""}>week</option>
          <option value="month" {"selected" if timeframe_value=="month" else ""}>month</option>
          <option value="year" {"selected" if timeframe_value=="year" else ""}>year</option>
        </select>
      </div>
      <div class="mb-3">
        <label class="form-label">Start Date</label>
        <select name="start_date_select" id="start_date_select" class="form-select">
          {options_html}
        </select>
      </div>
      <div id="custom_date_div" class="mb-3" style="{custom_date_div_style}">
        <label class="form-label">Custom Date (YYYY-MM-DD)</label>
        <input type="text" name="start_date_custom" placeholder="YYYY-MM-DD" class="form-control" value="{custom_date}">
      </div>
      <div class="mb-3">
        <label class="form-label">Accumulate For</label>
        <select name="accumulate_period" class="form-select">
          <option value="0.5" {"selected" if accumulate_years_value=="0.5" else ""}>6 months</option>
          <option value="1" {"selected" if accumulate_years_value=="1" else ""}>1 year</option>
          <option value="2" {"selected" if accumulate_years_value=="2" else ""}>2 years</option>
          <option value="3" {"selected" if accumulate_years_value=="3" else ""}>3 years</option>
          <option value="4" {"selected" if accumulate_years_value=="4" else ""}>4 years</option>
          <option value="5" {"selected" if accumulate_years_value=="5" else ""}>5 years</option>
          <option value="6" {"selected" if accumulate_years_value=="6" else ""}>6 years</option>
          <option value="7" {"selected" if accumulate_years_value=="7" else ""}>7 years</option>
          <option value="8" {"selected" if accumulate_years_value=="8" else ""}>8 years</option>
          <option value="9" {"selected" if accumulate_years_value=="9" else ""}>9 years</option>
          <option value="10" {"selected" if accumulate_years_value=="10" else ""}>10 years</option>
        </select>
      </div>
      <div class="mb-3 form-check">
        <input type="checkbox" name="include_btc" class="form-check-input" {"checked" if include_btc=="on" else ""}>
        <label class="form-check-label">Include Bitcoin</label>
      </div>
    </form>
    """

    html = f"""
<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MicroStrategy & BTC DCA Tracker</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
      body {{
        background-color: #f8f9fa;
        padding-bottom: 20px;
      }}
      .navbar-brand {{
        font-weight: bold;
      }}
      .card {{
        margin-top: 20px;
      }}
      .form-control {{
        height: 40px;
      }}
      .form-label {{
        font-size: 0.9rem;
      }}
      .summary-container {{
        width: 100%;
        margin-bottom: 20px;
      }}
      .form-graph-row {{
        display: flex;
        flex-direction: column;
        gap: 20px;
      }}
      .input-container, .graph-container {{
        width: 100%;
      }}
      @media (min-width: 1024px) {{
        .form-graph-row {{
          flex-direction: row;
        }}
        .input-container {{
          width: 25%;
          flex: 1 1 0;
        }}
        .graph-container {{
          width: 75%;
          flex: 3 1 0;
        }}
      }}
    </style>
  </head>
  <body>
    <div class="container-fluid">
      <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
          <a class="navbar-brand" href="#">DCA Tracker</a>
          <button class="navbar-toggler" type="button" data-bs-toggle="collapse" 
                  data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" 
                  aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
          </button>
          <div class="collapse navbar-collapse" id="navbarNav"></div>
        </div>
      </nav>
      <div class="container mt-4">
        <h1 class="text-center">MicroStrategy & BTC DCA Tracker</h1>
        <div class="row justify-content-center mt-4">
          <div class="col-12">
            <div class="summary-container" id="summary-area"></div>
            <div class="form-graph-row">
              <div class="input-container">
                <div class="card shadow-sm">
                  <div class="card-body">
                    {form_html}
                  </div>
                </div>
              </div>
              <div class="graph-container" id="graph-area"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
    function updateGraph() {{
      const form = document.getElementById('dca-form');
      const params = new URLSearchParams(new FormData(form));
      fetch('/graph?' + params.toString())
        .then(res => res.json())
        .then(data => {{
          document.getElementById('summary-area').innerHTML = data.summary_stats;
          document.getElementById('graph-area').innerHTML = data.graph_html;
          // Plotlyのscriptタグを実行
          document.getElementById('graph-area').querySelectorAll("script").forEach(oldScript => {{
            const newScript = document.createElement("script");
            if (oldScript.src) {{
              newScript.src = oldScript.src;
            }} else {{
              newScript.textContent = oldScript.textContent;
            }}
            document.body.appendChild(newScript);
            document.body.removeChild(newScript);
          }});
        }});
    }}
    // すべての入力欄にイベントを付与
    document.querySelectorAll('#dca-form input, #dca-form select').forEach(el => {{
      el.addEventListener('input', updateGraph);
      el.addEventListener('change', updateGraph);
    }});
    // カスタム日付欄の表示制御
    document.getElementById('start_date_select').addEventListener('change', function() {{
      var customDiv = document.getElementById('custom_date_div');
      if (this.value === 'custom') {{
          customDiv.style.display = 'block';
      }} else {{
          customDiv.style.display = 'none';
      }}
    }});
    // ページロード時に一度グラフを表示
    window.addEventListener('DOMContentLoaded', updateGraph);
    </script>
  </body>
</html>

"""
    return render_template_string(html)


if __name__ == "__main__":
    app.run(debug=True)
