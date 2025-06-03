def load_data(source):
    import yfinance as yf
    import pandas as pd

    if source == "MSTR":
        df = yf.download("MSTR", start="2010-01-01")
        df.reset_index(inplace=True)
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        return df
    elif source == "BTC-USD":
        df = yf.download("BTC-USD", start="2010-01-01")
        df.reset_index(inplace=True)
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        return df

    if source.endswith(".csv"):
        data = pd.read_csv(source)
    else:
        raise ValueError("Unsupported data source format. Please provide a CSV file.")

    # Process the data as needed
    data["Date"] = pd.to_datetime(data["Date"])
    data.set_index("Date", inplace=True)

    return data
