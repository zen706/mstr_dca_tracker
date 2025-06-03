import pandas as pd


class DCA_Calculator:
    def __init__(
        self,
        investment_amount,
        timeframe,
        historical_data,
        start_date=None,
        accumulate_years=None,
    ):
        self.investment_amount = investment_amount
        self.timeframe = timeframe
        self.historical_data = historical_data
        # 開始日が指定されていなければ、データの最初の日付を使用
        self.start_date = (
            pd.to_datetime(start_date) if start_date else historical_data.index.min()
        )
        self.accumulate_years = accumulate_years

    def calculate_returns(self):
        returns = []
        total_units = 0
        # 指定された期間に合わせてデータをリサンプリング
        if self.timeframe == "week":
            resampled = self.historical_data.resample("W").first()
        elif self.timeframe == "month":
            resampled = self.historical_data.resample("M").first()
        elif self.timeframe == "day":
            resampled = self.historical_data
        else:
            resampled = self.historical_data.resample("Y").first()

        # 対象期間に絞り込む
        resampled = resampled[resampled.index >= self.start_date]
        if self.accumulate_years:
            end_date = self.start_date + pd.DateOffset(years=self.accumulate_years)
            resampled = resampled[resampled.index <= end_date]

        for date, row in resampled.iterrows():
            price = row["Close"]
            if isinstance(price, pd.Series):
                price = price.iloc[0]
            if pd.isna(price):
                continue
            units = self.investment_amount / price
            total_units += units
            current_value = total_units * price
            returns.append({"date": date, "value": current_value})

        return returns

    def get_investment_data(self):
        return self.historical_data
