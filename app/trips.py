import pandas as pd

def add_pickup_day(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["pickup_day"] = df["tpep_pickup_datetime"].dt.strftime("%Y-%m-%d")
    return df


# tip_percentage: how much people tip, as a percentage of the fare
def tip_percentage(df: pd.DataFrame) -> pd.Series:
    return df["tip_amount"] * 100 / df["fare_amount"]