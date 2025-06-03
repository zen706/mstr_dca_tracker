from flask import Flask, request, render_template_string
import pandas as pd
import plotly.graph_objects as go
from dca.data_loader import load_data
from dca.calculator import DCA_Calculator

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    # フォームで入力された値（無い場合は初期値を設定）
    investment_value = request.args.get("investment", "10")
    timeframe_value = request.args.get("timeframe", "week")
    start_date_value = request.args.get("start_date", "2015-01-01")
    accumulate_years_value = request.args.get("accumulate_years", "5")
    include_btc = request.args.get("include_btc", "off")  # "on"ならチェック済み

    # 入力フォーム部分にBTC選択チェックボックスを追加
    form_html = f"""
    <form action="/" method="get">
      Investment Amount: <input type="text" name="investment" value="{investment_value}"><br>
      Timeframe:
      <select name="timeframe">
        <option value="day" {"selected" if timeframe_value=="day" else ""}>day</option>
        <option value="week" {"selected" if timeframe_value=="week" else ""}>week</option>
        <option value="month" {"selected" if timeframe_value=="month" else ""}>month</option>
        <option value="year" {"selected" if timeframe_value=="year" else ""}>year</option>
      </select><br>
      Start Date (YYYY-MM-DD): <input type="text" name="start_date" value="{start_date_value}"><br>
      Accumulate For (years): <input type="text" name="accumulate_years" value="{accumulate_years_value}"><br>
      <label>
         <input type="checkbox" name="include_btc" {"checked" if include_btc=="on" else ""}>
         Include Bitcoin
      </label><br>
      <input type="submit" value="Calculate">
    </form>
    """

    results_html = ""
    if "investment" in request.args:
        try:
            # 入力値取得
            investment = float(investment_value)
            timeframe = timeframe_value.lower()
            start_date = start_date_value
            accumulate_years = (
                int(accumulate_years_value) if accumulate_years_value else None
            )

            # ① MSTR のデータ取得とDCA計算
            historical_data_mstr = load_data("MSTR")
            dca_calculator_mstr = DCA_Calculator(
                investment,
                timeframe,
                historical_data_mstr,
                start_date,
                accumulate_years,
            )
            returns_mstr = dca_calculator_mstr.calculate_returns()
            dates_mstr = [data["date"] for data in returns_mstr]
            values_mstr = [data["value"] for data in returns_mstr]
            cumulative_investment_mstr = investment * len(returns_mstr)

            # Plotly グラフの作成
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

            summary_html = (
                f"<p>MSTR Cumulative Investment: ${cumulative_investment_mstr:.2f}</p>"
            )

            # ② チェックが入っていればBTCも取得・計算
            if include_btc == "on":
                historical_data_btc = load_data("BTC-USD")
                dca_calculator_btc = DCA_Calculator(
                    investment,
                    timeframe,
                    historical_data_btc,
                    start_date,
                    accumulate_years,
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
                summary_html += f"<p>BTC Cumulative Investment: ${cumulative_investment_btc:.2f}</p>"

            fig.update_layout(
                title="DCA Investment Returns",
                xaxis_title="Date",
                yaxis_title="Portfolio Value (USD)",
                yaxis_type="log",
            )

            graph_html = fig.to_html(full_html=False)
            results_html = (
                f"<h2>Results</h2>{summary_html}{{% raw %}}{graph_html}{{% endraw %}}"
            )
        except Exception as e:
            results_html = f"<p style='color:red;'>Error: {str(e)}</p>"

    html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>MicroStrategy & BTC DCA Tracker</title>
        <meta charset="utf-8">
        <!-- Bootstrap CDN -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
          body {{
            background-color: #f8f9fa;
          }}
          .card {{
            margin-top: 20px;
          }}
        </style>
      </head>
      <body>
        <div class="container">
          <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <a class="navbar-brand" href="#">DCA Tracker</a>
          </nav>
          <div class="row">
            <div class="col-md-12">
              <h1 class="mt-4">MicroStrategy & BTC DCA Tracker</h1>
              <div class="card">
                <div class="card-body">
                  {form_html}
                </div>
              </div>
              <div class="card">
                <div class="card-body">
                  {results_html}
                </div>
              </div>
            </div>
          </div>
        </div>
        <!-- Bootstrap JS（任意） -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
      </body>
    </html>
    """
    return render_template_string(html)


if __name__ == "__main__":
    app.run(debug=True)
