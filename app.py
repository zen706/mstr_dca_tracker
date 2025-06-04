from flask import Flask, request, render_template_string
import pandas as pd
import plotly.graph_objects as go
from dca.data_loader import load_data
from dca.calculator import DCA_Calculator
from datetime import datetime
from dateutil.relativedelta import relativedelta

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    # 初期値
    investment_value = request.args.get("investment", "10")
    timeframe_value = request.args.get("timeframe", "week")
    accumulate_years_value = request.args.get("accumulate_period", "5")
    include_btc = request.args.get("include_btc", "off")  # "on"ならチェック済み

    # ここで start_date_select を取得
    start_date_select = request.args.get("start_date_select")
    # custom_dateの値を取得
    custom_date = request.args.get("start_date_custom", "")
    # custom_date_divの表示状態を決定
    if start_date_select == "custom":
        custom_date_div_style = "display: block;"
    else:
        custom_date_div_style = "display: none;"

    # 開始日セレクトボックス用のオプションを作成（半年前、1年前～10年前）
    today = datetime.today()
    options = []
    # 半年前
    half_year = today - relativedelta(months=6)
    options.append(("6months", half_year.strftime("%Y-%m-%d"), "6 months ago"))
    # 1年前～10年前
    for i in range(1, 11):
        option_date = today - relativedelta(years=i)
        options.append((f"{i}year", option_date.strftime("%Y-%m-%d"), f"{i} year ago"))

    # 選択肢HTMLの生成（日付の部分は表示しない）
    options_html = ""
    for value, date_str, label in options:
        selected = " selected" if start_date_select == date_str else ""
        options_html += f'<option value="{date_str}"{selected}>{label}</option>'
    # 最後に任意日付選択用のオプション
    custom_selected = " selected" if start_date_select == "custom" else ""
    options_html += f'<option value="custom"{custom_selected}>Custom Date</option>'

    # フォームのHTML（「Start Date:」ラベルを表示）
    # フォーム HTML 部分の更新例
    # フォーム HTML 部分の更新例（一部抜粋）
    form_html = f"""
    <form id="dca-form" action="/" method="get" autocomplete="off">
      <div class="mb-3">
        <label class="form-label">Investment Amount</label>
        <div class="input-group">
          <span class="input-group-text">$</span>
          <input type="number" name="investment" value="{investment_value}" class="form-control" step="1" min="1" oninput="autoSubmit()">
        </div>
      </div>
      <div class="mb-3">
        <label class="form-label">Timeframe</label>
        <select name="timeframe" class="form-select" onchange="autoSubmit()">
          <option value="day" {"selected" if timeframe_value=="day" else ""}>day</option>
          <option value="week" {"selected" if timeframe_value=="week" else ""}>week</option>
          <option value="month" {"selected" if timeframe_value=="month" else ""}>month</option>
          <option value="year" {"selected" if timeframe_value=="year" else ""}>year</option>
        </select>
      </div>
      <div class="mb-3">
        <label class="form-label">Start Date</label>
        <select name="start_date_select" id="start_date_select" class="form-select" onchange="autoSubmit()">
          {options_html}
        </select>
      </div>
      <div id="custom_date_div" class="mb-3" style="{custom_date_div_style}">
        <label class="form-label">Custom Date (YYYY-MM-DD)</label>
        <input type="text" name="start_date_custom" placeholder="YYYY-MM-DD" class="form-control" value="{custom_date}" oninput="autoSubmit()">
      </div>
      <div class="mb-3">
        <label class="form-label">Accumulate For</label>
        <select name="accumulate_period" class="form-select" onchange="autoSubmit()">
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
        <input type="checkbox" name="include_btc" class="form-check-input" {"checked" if include_btc=="on" else ""} onchange="autoSubmit()">
        <label class="form-check-label">Include Bitcoin</label>
      </div>
    </form>
    <script>
      // 入力値が変わったら自動送信
      function autoSubmit() {{
        document.getElementById('dca-form').submit();
      }}
      // 選択値が「custom」のときだけ、カスタム入力欄を表示する
      document.getElementById('start_date_select').addEventListener('change', function() {{
          var customDiv = document.getElementById('custom_date_div');
          if (this.value === 'custom') {{
              customDiv.style.display = 'block';
          }} else {{
              customDiv.style.display = 'none';
          }}
      }});
    </script>
    """
    # サーバ側でstart_dateを決定
    start_date_select = request.args.get("start_date_select")
    if start_date_select == "custom":
        start_date = request.args.get("start_date_custom", "2015-01-01")
    elif start_date_select:
        start_date = start_date_select
    else:
        # 初回アクセス時のデフォルト
        start_date = "2015-01-01"

    results_html = ""
    if "investment" in request.args:
        try:
            investment = float(investment_value)
            timeframe = timeframe_value.lower()
            # accumulate_years_value を float に変換
            acc_val = float(accumulate_years_value) if accumulate_years_value else 0
            if acc_val < 1:
                # 例: "0.5" → 6 months
                accumulate_period = int(acc_val * 12)
            else:
                accumulate_period = int(acc_val)

            # ① MSTR のデータ取得と DCA 計算
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

            # 動的にサマリーステータスを算出
            total_invested = cumulative_investment_mstr
            total_value = values_mstr[-1] if values_mstr else 0
            percent_change = (
                (total_value / total_invested * 100) if total_invested > 0 else 0
            )

            # BTC の最新価格を取得
            btc_df = load_data("BTC-USD")
            current_btc_usd = btc_df["Close"].iloc[-1]

            # MSTR の最新株価を取得
            mstr_df = load_data("MSTR")
            current_mstr_price = mstr_df["Close"].iloc[-1]

            import math

            sat_value_calculated = math.floor((total_value / current_btc_usd) * 10**8)
            mstr_shares_calculated = math.floor(total_value / current_mstr_price)

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

            # BTC の積立計算とグラフへの追加（if include_btc=="on"の場合のみ）
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
            # MSTRサマリーステータス
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
            # 両方のサマリーステータスを連結（BTCは含む場合のみ）
            if include_btc == "on":
                summary_stats = summary_stats + summary_stats_btc

            fig.update_layout(
                title="DCA Investment Returns",
                xaxis_title="Date",
                yaxis_title="Portfolio Value (USD)",
                yaxis_type="log",
            )

            graph_html = fig.to_html(full_html=False)
            results_html = f"{{% raw %}}{graph_html}{{% endraw %}}"

        except Exception as e:
            results_html = f"<p style='color:red;'>Error: {str(e)}</p>"
            summary_stats = ""

    html = f"""
<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="utf-8">
    <!-- レスポンシブ対応 -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MicroStrategy & BTC DCA Tracker</title>
    <!-- Bootstrap CDN -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
  body {{
    background-color: #f8f9fa;
    padding-bottom: 20px; /* 下端に余白 */
  }}
  .navbar-brand {{
    font-weight: bold;
  }}
  .card {{
    margin-top: 20px;
  }}
  /* Bootstrap の form-control を利用（必要なら高さを明示する） */
  .form-control {{
    height: 40px;
  }}
  /* ラベルのフォントサイズをフォームのフォントより若干小さく */
  .form-label {{
    font-size: 0.9rem;
  }}
  /* 各フォーム項目間に余白を追加（mb-3 は Bootstrap のユーティリティクラスなので不要なら独自設定も可能） */
  /* 1280px以上の場合に横並びレイアウトはそのまま */
  @media (min-width: 1280px) {{
    .input-results-container {{
      display: flex;
      gap: 20px;
      width: 100%;
    }}
    .input-container {{
      flex: 1;
    }}
    .results-container {{
      flex: 2;
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
          <div class="collapse navbar-collapse" id="navbarNav">
          </div>
        </div>
      </nav>
      <div class="container mt-4">
        <h1 class="text-center">MicroStrategy & BTC DCA Tracker</h1>
        {summary_stats}
        <div class="row justify-content-center mt-4">
          <!-- ここでは col-lg-8 ではなく、画面余白内でいっぱい使うため col-12 とする -->
          <div class="col-12 input-results-container">
            <div class="input-container">
              <div class="card shadow-sm">
                <div class="card-body">
                  {form_html}
                </div>
              </div>
            </div>
            <div class="results-container mt-4 mt-lg-0">
              <div class="card shadow-sm">
                <div class="card-body">
                  {results_html}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  </body>
</html>
"""
    return render_template_string(html)


if __name__ == "__main__":
    app.run(debug=True)
