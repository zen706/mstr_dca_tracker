import matplotlib.pyplot as plt


class Visualizer:
    def __init__(self):
        pass

    def plot_returns(self, returns_data):
        # returns_dataを使ってグラフを描画
        # 例:
        dates = [r["date"] for r in returns_data]
        values = [r["value"] for r in returns_data]
        plt.figure(figsize=(10, 5))
        plt.plot(dates, values, marker="o")
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value")
        plt.title("DCA Investment Returns")
        plt.grid(True)
        plt.tight_layout()
        plt.show()
