# CI/CD practice session for Agile Data Science class

In this session you add continuous integration to the repository from the
storage session: a first [GitHub Actions](https://docs.github.com/en/actions)
workflow, tests and lint on every pull request, and a rule that blocks merging
when a check is red.

## Starting point

This session continues from the storage session. You need its final state:
`upload.py`, `read_remote.py`, `formats.py`, `compose.yaml` and the `app`
folder.

### If you finished the storage session

Keep working in your `ub-agile-data-science-storage` repository:

```bash
cd ub-agile-data-science-storage
git checkout main
git pull
source .venv/bin/activate
```

### If you did not finish it, or missed it

This repository has the final state of the storage session. Start from a copy
of it.

On GitHub, create a new repository called `ub-agile-data-science-ci`. Leave it
**empty**: no README, no `.gitignore`, no license.

Clone this repository and push it to yours:

- note: substitute `${YOUR_USER}` for your username on GitHub

```bash
git clone https://github.com/raulcd/ub-agile-data-science-ci.git
cd ub-agile-data-science-ci
git remote set-url origin git@github.com:${YOUR_USER}/ub-agile-data-science-ci.git
git push -u origin main
```

Create a virtual environment and install the requirements. `pandas` 3 needs
Python 3.11 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, from `git bash`, activate it with `source .venv/Scripts/activate`.

Download the data, around 50 MB. One question in Exercise 2 uses it:

```bash
mkdir data
curl -L -o data/yellow_tripdata_2024-01.parquet \
  https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet
```

### In both cases

Your repository has to be **public**: Actions minutes are unlimited for public
repositories, and rulesets (Exercise 3) need it on a free account.

## Exercise 1: your first workflow

Create the file `.github/workflows/hello.yml`. The folder name matters,
GitHub only looks for workflows there:

```yaml
name: Hello

on:
  push:
  workflow_dispatch:

jobs:
  hello:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - run: echo "Hello ${{ github.actor }}, this is ${{ github.ref_name }}"
      - run: ls -la
      - run: python --version
```

Commit and push:

```bash
git add .github/workflows/hello.yml
git commit -m "Add a first workflow"
git push
```

Open your repository on GitHub and go to the **Actions** tab. You will see a
run called "Add a first workflow", the commit message. Click on it, then on
the `hello` job, and open each step to read its output.

On the left, click **Hello**. A **Run workflow** button shows up: that is the
`workflow_dispatch` trigger. Run it again by hand.

Add a step that prints how many CPUs the machine has:

```yaml
      - run: nproc
```

Push again and check the new run.

Questions:

- `ls -la` lists your files, but there is no `data` folder. Why?
- Remove the `actions/checkout@v7` step and push. What does `ls -la` show now?
  Put it back.

## Exercise 2: tests and lint on every pull request

Work on a branch:

```bash
git checkout -b add-tests
```

### Some code to test

Create a new file `trips.py` with two functions:

```python
import pandas as pd


def add_pickup_day(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["pickup_day"] = df["tpep_pickup_datetime"].dt.strftime("%Y-%m-%d")
    return df


def tip_percentage(df: pd.DataFrame) -> pd.Series:
    return df["tip_amount"] * 100 / df["fare_amount"]
```

- `add_pickup_day` adds the day of each trip, as `2024-01-15`.
- `tip_percentage` computes how much people tip, as a percentage of the fare.

### Write the tests

Create `test_trips.py`. pytest runs every function whose name starts with
`test_` in files whose name starts with `test_`:

```python
import pandas as pd

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
```

The tests use tiny DataFrames where you know the answer: no bucket, no 3
million rows.

The tools to test are not needed to run the app, so they go in their own
file. Create `requirements-dev.txt`:

```
-r requirements.txt
pytest==9.1.1
```

Install it and run the tests:

```bash
pip install -r requirements-dev.txt
pytest
```

One test fails:

```
test_trips.py ..F                                                        [100%]

=================================== FAILURES ===================================
________________ test_tip_percentage_ignores_trips_without_fare ________________

    def test_tip_percentage_ignores_trips_without_fare():
        trips = pd.DataFrame({"fare_amount": [10.0, 0.0, -5.0], "tip_amount": [2.0, 1.0, 0.0]})
>       assert tip_percentage(trips).mean() == 20.0
E       assert np.float64(inf) == 20.0
...
FAILED test_trips.py::test_tip_percentage_ignores_trips_without_fare - assert...
========================= 1 failed, 2 passed in 0.18s ==========================
```

**Do not fix it yet.** First let CI find it.

pytest leaves a cache folder behind. Add it to `.gitignore`:

```
.pytest_cache/
```

### Run the tests on CI

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.14"
      - run: pip install -r requirements-dev.txt
      - run: pytest
```

It runs on every pull request, and on every push to `main` (after a merge).
`actions/setup-python` installs the Python version you choose, instead of
using the one the runner happens to have.

Commit and push the branch, with the failing test:

```bash
git add .gitignore trips.py test_trips.py requirements-dev.txt .github/workflows/ci.yml
git commit -m "Add tests and CI"
git push -u origin add-tests
```

On GitHub, open a pull request from `add-tests` to `main`. At the bottom of
the pull request you will see the `test` check running. It goes red. Click on
**Details** next to it: it is the same pytest output you got on your laptop.

### Fix the bug

Dividing by a fare of 0 gives `inf`, without any error, and a single `inf`
makes the mean `inf`. This is not a made-up case: check how many trips in
`data/yellow_tripdata_2024-01.parquet` have a fare of 0, and how many a negative one.

Fix `tip_percentage` so it only uses trips with a fare greater than 0. Run
`pytest` until you see:

```
============================== 3 passed in 0.17s ===============================
```

Commit and push to the same branch:

```bash
git commit -am "Ignore trips without fare in tip_percentage"
git push
```

Go back to the pull request. The checks run again on the new commit, and
`test` goes green.

What is the average tip percentage on the real January data?

### Lint

A linter reads your code without running it and reports mistakes and style
problems. Add [Ruff](https://docs.astral.sh/ruff/) to `requirements-dev.txt`:

```
-r requirements.txt
pytest==9.1.1
ruff==0.17.1
```

Install it and run it:

```bash
pip install -r requirements-dev.txt
ruff check .
```

```
PLR0402 [*] Use `from pyarrow import fs` in lieu of alias
 --> app/app.py:4:8
...
Found 3 errors.
[*] 3 fixable with `--fix`.
```

Read what it suggests, then let it fix them:

```bash
ruff check --fix .
ruff check .
```

Run `pytest` again: a fix should never break a test.

Ruff also leaves a cache folder behind. Add it to `.gitignore`:

```
.ruff_cache/
```

Add a `lint` job to `ci.yml`, under `jobs:` next to `test`:

```yaml
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.14"
      - run: pip install -r requirements-dev.txt
      - run: ruff check .
```

The two jobs run in parallel, each on its own machine. That is why both
install the requirements.

Commit and push to the same branch:

```bash
git add .gitignore requirements-dev.txt upload.py read_remote.py app/app.py \
  .github/workflows/ci.yml
git commit -m "Add lint"
git push
```

The pull request now shows two checks, `lint` and `test`. Wait until both are
green and merge it.

Questions:

- Go to the Actions tab. Which workflows ran for your pull request, and why
  did `Hello` run too?
- `hello.yml` has done its job. Delete it in your next pull request.

## Exercise 3: a red check blocks the merge

The checks report, but nothing stops you from merging a red pull request. Make
them required.

On GitHub, go to **Settings → Rules → Rulesets → New ruleset → New branch
ruleset**:

- Ruleset name: `main`
- Enforcement status: **Active**
- Target branches: **Add target → Include default branch**
- Check **Require a pull request before merging**. Leave the required
  approvals at 0, you cannot approve your own pull requests
- Check **Require status checks to pass**, click **Add checks** and add
  `lint` and `test`. GitHub only suggests checks that ran in the last days:
  that is why you merged a pull request first
- Click **Create**

Try to push directly to `main`:

```bash
git checkout main
git pull
git commit --allow-empty -m "Straight to main"
git push
```

Read the error, then drop that commit:

```bash
git reset --hard origin/main
```

Now break a test on purpose. Create a branch and change the format of the day
in `trips.py`:

```python
    df["pickup_day"] = df["tpep_pickup_datetime"].dt.strftime("%d/%m/%Y")
```

```bash
git checkout -b day-format
git commit -am "Use day/month/year"
git push -u origin day-format
```

Open a pull request. The `test` check goes red and the merge button is
blocked. Click on **Details** next to the failed check: it is the same pytest
output you get on your laptop.

Put the format back, commit and push to the same branch. The checks run again
on the same pull request. When they are green, merge it.

Questions:

- A teammate says "it passes on my laptop", but the check is red. Who is
  right? What could be different between their laptop and the runner?
- The tests only check `trips.py`. Nothing checks that `upload.py` still
  runs. What would you need to run it in CI?

## Extra: use the functions in upload.py

`upload.py` from the storage session keeps the January trips and adds the day
inline:

```python
jan = df[df["tpep_pickup_datetime"].between("2024-01-01", "2024-02-01")].copy()
jan["pickup_day"] = jan["tpep_pickup_datetime"].dt.strftime("%Y-%m-%d")
```

Code inside a script is hard to test. Move it into `trips.py`, test it there,
and call it from the script.

Create a branch:

```bash
git checkout main
git pull
git checkout -b upload-uses-trips
```

Add a function to `trips.py`:

```python
def keep_month(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    pickup = df["tpep_pickup_datetime"]
    return df[(pickup.dt.year == year) & (pickup.dt.month == month)]
```

Add `keep_month` to the import in `test_trips.py`, and a test:

```python
def test_keep_month_drops_wrong_dates():
    trips = pd.DataFrame({"tpep_pickup_datetime": pd.to_datetime(
        ["2002-12-31 23:00:00", "2024-01-15 08:30:00", "2009-01-01 00:10:00"])})
    assert len(keep_month(trips, 2024, 1)) == 1
```

In `upload.py`, import the functions next to the other imports:

```python
from trips import add_pickup_day, keep_month
```

and replace the two lines above with:

```python
jan = add_pickup_day(keep_month(df, 2024, 1))
```

Run `pytest` and `ruff check .`. If you have the storage server running and
the files from `formats.py` in `data/`, run `upload.py` again: the bucket
should have the same 31 days.

Commit, push the branch and open a pull request. Merge it when the checks are
green.

# Experiment tracking with MLflow

In this session you train a model on the taxi trips and keep track of every
run with [MLflow](https://mlflow.org/): its parameters, its metrics and the
model it produced.

The model predicts how long a trip takes, in minutes, from its distance, the
hour and day of the week of the pickup, and the pickup and dropoff zones.

## Exercise 1: your first run

`main` is protected since the last session: work on a branch and open a pull
request at the end.

```bash
git checkout main
git pull
git checkout -b first-run
```

### Install MLflow

Add `mlflow` and `scikit-learn` to `requirements.txt`. MLflow 3.17 does not
support `pyarrow` 26 yet, so change its pin to 25:

```
pandas==3.0.6
pyarrow==25.0.0
mlflow==3.17.2
scikit-learn==1.9.1
```

Install them in your virtual environment:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Prepare the data

The model reads `data/trips.parquet`, the file `formats.py` wrote in the
storage session. If you do not have it, copy the file you downloaded:

```bash
cp data/yellow_tripdata_2024-01.parquet data/trips.parquet
```

Create a file `features.py`. It computes the duration of each trip and the
features, keeps 100,000 trips so a run takes seconds, and splits them in a
training and a test set:

```python
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
```

### Train and log a run

Create a file `train.py`:

```python
import mlflow
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from features import load_trips

X_train, X_test, y_train, y_test = load_trips()

mlflow.set_experiment("trip-duration")

with mlflow.start_run():
    params = {"n_estimators": 50, "max_depth": 5}
    mlflow.log_params(params)

    model = RandomForestRegressor(**params, random_state=42)
    model.fit(X_train, y_train)

    mae = mean_absolute_error(y_test, model.predict(X_test))
    mlflow.log_metric("mae", mae)
    mlflow.sklearn.log_model(
        model,
        name="model",
        input_example=X_test[:5],
        # skops only loads types it knows are safe. Tree models must
        # be trusted explicitly: only for models you trust.
        skops_trusted_types=["sklearn.tree._tree.Tree"],
    )
    print(f"MAE: {mae:.2f} minutes")
```

Run it:

```bash
python train.py
```

MLflow prints a few log lines and warnings. At the end you should see:

```
MAE: 3.81 minutes
```

On average, the model is almost 4 minutes off.

### Look at the run

MLflow wrote two things next to your code: `mlflow.db`, a SQLite database with
the parameters and metrics, and `mlruns/`, with the model files. Neither
belongs in Git. Add them to `.gitignore`:

```
mlflow.db
mlruns/
```

Start the MLflow UI:

```bash
mlflow ui --port 5050
```

Open http://localhost:5050 and click on the `trip-duration` experiment. Your
run has a random name. Click on it and find:

- the parameters, `n_estimators` and `max_depth`
- the metric, `mae`
- the model in the **Artifacts** tab: the `MLmodel` file, `requirements.txt`
  and the input example

Leave the UI running and open a second terminal for the next step. Activate
the virtual environment there too.

### A second run

In `train.py`, change `max_depth` to 10 and run it again:

```bash
python train.py
```

```
MAE: 3.44 minutes
```

Reload the UI: the experiment now has two runs. Select both and click
**Compare**.

### Open a pull request

```bash
git add requirements.txt .gitignore features.py train.py
git commit -m "Train a first model and track it with MLflow"
git push -u origin first-run
```

Open a pull request and merge it when the checks are green.

Questions:

- You change `train.py` and commit without running it. How do you know which
  run used which version of the code? Look at the run's details in the UI.
- Delete `mlflow.db` and reload the UI. What happened to your runs? What would
  happen if your laptop broke?
