import pandas as pd
from sklearn.model_selection import train_test_split

FEATURES = ["trip_distance", "pickup_hour", "pickup_weekday",
            "PULocationID", "DOLocationID"]

def load_trips(path="data/trips.parquet", n=100_000):
    df = pd.read_parquet(path)
    df["duration_min"] = (
        df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
    ).dt.total_seconds() / 60
    df["pickup_hour"] = df["tpep_pickup_datetime"].dt.hour
    df["pickup_weekday"] = df["tpep_pickup_datetime"].dt.weekday
    # Drop trips of less than a minute or more than two hours
    df = df[df["duration_min"].between(1, 120)]
    df = df.sample(n, random_state=42)
    X = df[FEATURES].astype("float64")
    return train_test_split(X, df["duration_min"],
                            test_size=0.2, random_state=42)
