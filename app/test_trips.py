import pandas as pd
from app import trips
from trips import add_pickup_day, tip_percentage

def test_add_pickup_day():
    trips = pd.DataFrame({"tpep_pickup_datetime": pd.to_datetime(["2024-01-15 08:30:00"])})
    assert add_pickup_day(trips)["pickup_day"].tolist() == ["2024-01-15"]

def test_tip_percentage():
    trips = pd.DataFrame({"fare_amount": [10.0, 20.0], "tip_amount": [2.0, 3.0]})
    assert tip_percentage(trips).tolist() == [20.0, 15.0]

def test_tip_percentage_ignores_trips_without_fare():
    trips = pd.DataFrame({"fare_amount": [10.0, 0.0, -5.0], "tip_amount": [2.0, 1.0, 0.0]})
    assert tip_percentage(trips).mean() == 20.0
