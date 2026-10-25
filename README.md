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

## Exercise 2: compare runs

```bash
git checkout main
git pull
git checkout -b compare-runs
```

### Many runs

Trying parameters by hand, one run at a time, does not scale. Create a file
`train_many.py` that trains one model for each `max_depth`:

```python
import mlflow
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from features import load_trips

X_train, X_test, y_train, y_test = load_trips()

mlflow.set_experiment("trip-duration")

for max_depth in [2, 5, 10, 20]:
    with mlflow.start_run(run_name=f"rf-depth-{max_depth}"):
        params = {"n_estimators": 50, "max_depth": max_depth}
        mlflow.log_params(params)
        model = RandomForestRegressor(**params, random_state=42)
        model.fit(X_train, y_train)
        mae = mean_absolute_error(y_test, model.predict(X_test))
        mlflow.log_metric("mae", mae)
        mlflow.sklearn.log_model(
            model,
            name="model",
            input_example=X_test[:5],
            skops_trusted_types=["sklearn.tree._tree.Tree"],
        )
        print(f"max_depth={max_depth:2}  MAE: {mae:.2f} minutes")
```

`run_name` gives each run a readable name instead of a random one. Run it, it
takes around 20 seconds:

```bash
python train_many.py
```

```
max_depth= 2  MAE: 4.52 minutes
max_depth= 5  MAE: 3.81 minutes
max_depth=10  MAE: 3.44 minutes
max_depth=20  MAE: 3.32 minutes
```

### Compare them in the UI

If the UI is not running, start it again with `mlflow ui --port 5050`.

In the `trip-duration` experiment:

- Add the `mae` column to the table if it is not there, and sort by it
- Select the four `rf-depth-*` runs and click **Compare**: parameters side by
  side, and plots of the metrics against the parameters
- Switch to the chart view and plot `mae` against `max_depth`

### How big is each model?

The best MAE is not the only thing that matters. Log the size of each model
as a metric. Add `import pickle` at the top of `train_many.py` and, after
`log_metric("mae", mae)`:

```python
        mlflow.log_metric("size_mb", len(pickle.dumps(model)) / 1e6)
```

Run it again and compare `size_mb` against `max_depth` in the chart view.

### Find the best run from code

The UI is for people. A script can ask the same question. Open a Python shell:

```bash
python
```

```python
import mlflow

best = mlflow.search_runs(
    experiment_names=["trip-duration"],
    order_by=["metrics.mae ASC"],
    max_results=1,
).iloc[0]
print(best["tags.mlflow.runName"], best["metrics.mae"])
```

```
rf-depth-20 3.319029923858316
```

`search_runs` returns a pandas DataFrame, one row per run. Type
`mlflow.search_runs(experiment_names=["trip-duration"])` to see all of them,
and `exit()` to leave the shell.

### Open a pull request

```bash
git add train_many.py
git commit -m "Train one model per max_depth"
git push -u origin compare-runs
```

Open a pull request and merge it when the checks are green.

Questions:

- `rf-depth-20` has the best MAE. Look at its `size_mb`. Which model would you
  put in production, and why?
- Add `n_estimators` to the loop, with values `[10, 50]`, and include it in
  the `run_name`. How many runs do you get? Do not commit this change.

## Exercise 3: a shared tracking server

Your runs live in `mlflow.db` and `mlruns/`, on your laptop. Nobody else can
see them. In this exercise you run an MLflow server with Docker Compose. It
keeps parameters and metrics in a database and the model files in a bucket,
on the RustFS server from the storage session.

```bash
git checkout main
git pull
git checkout -b tracking-server
```

### The server image

The official MLflow image does not include `boto3`, the library MLflow uses to
talk to S3. Create a file `server/Dockerfile` that adds it:

```dockerfile
FROM ghcr.io/mlflow/mlflow:v3.17.2
RUN pip install --no-cache-dir boto3==1.40.70
```

### Add the server to compose.yaml

Add an `mlflow` service to `compose.yaml`, next to `storage` and `web`, and a
`mlflowdb` volume for its database. The file should look like this:

```yaml
services:
  storage:
    image: rustfs/rustfs:1.0.1
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      RUSTFS_ACCESS_KEY: student
      RUSTFS_SECRET_KEY: student-secret
    volumes:
      - s3data:/data

  web:
    build: ./app
    ports:
      - "5001:5000"
    environment:
      S3_ENDPOINT: http://storage:9000
      AWS_ACCESS_KEY_ID: student
      AWS_SECRET_ACCESS_KEY: student-secret
      AWS_REGION: us-east-1
    depends_on:
      - storage

  mlflow:
    build: ./server
    ports:
      - "5050:5000"
    environment:
      MLFLOW_S3_ENDPOINT_URL: http://storage:9000
      AWS_ACCESS_KEY_ID: student
      AWS_SECRET_ACCESS_KEY: student-secret
    command: >
      mlflow server --host 0.0.0.0 --port 5000
      --backend-store-uri sqlite:////mlflow/mlflow.db
      --artifacts-destination s3://mlflow
    volumes:
      - mlflowdb:/mlflow
    depends_on:
      - storage

volumes:
  s3data:
  mlflowdb:
```

- `--backend-store-uri`: where parameters, metrics and runs go. A SQLite file
  in the `mlflowdb` volume
- `--artifacts-destination`: where the model files go. The `mlflow` bucket
- The server has the bucket credentials. Your laptop will only need the
  server's URL

The server uses port 5050 on your laptop, the same as `mlflow ui`. Stop the
local UI first with `Ctrl+C`.

### Start it

```bash
docker compose up -d --build
```

The first time it downloads the MLflow image, it takes a few minutes.

Open the RustFS console at http://localhost:9001, log in with `student` /
`student-secret`, and create a bucket called `mlflow`. Without it, logging a
model fails with `too many 500 error responses`.

Open the MLflow UI at http://localhost:5050. It is empty: this is a new
server, your local runs are still in `mlflow.db`.

### Log runs to the server

Your code does not change. Tell MLflow where the server is with an
environment variable:

```bash
export MLFLOW_TRACKING_URI=http://localhost:5050
python train_many.py
```

Set it in **every terminal** you use from now on. Without it, MLflow goes
back to your local `mlflow.db`.

The `rf-depth-20` model is around 220 MB, its upload takes a little longer.

Reload the UI at http://localhost:5050: the runs are there. In the RustFS
console, open the `mlflow` bucket and follow the folders down to a model's
`artifacts`: the `MLmodel` file, `requirements.txt` and the model itself.

### Open a pull request

```bash
git add server/Dockerfile compose.yaml
git commit -m "Add an MLflow tracking server"
git push -u origin tracking-server
```

Open a pull request and merge it when the checks are green.

Questions:

- Run `docker compose down` and `docker compose up -d`. Are the runs still in
  the UI? Where are they stored? What would `docker compose down -v` do?
- Who has the bucket credentials: your laptop or the server? Why is that
  better for a team?
- Your local `mlflow.db` has the runs from Exercises 1 and 2. They are not on
  the server. What would you need to move them?

## Exercise 4: register and serve a model

Keep the server running and `MLFLOW_TRACKING_URI` set.

```bash
git checkout main
git pull
git checkout -b register-model
```

### Register the best run

A run id says nothing about what a model does. The Model Registry gives it a
name and versions. Create a file `register.py`:

```python
import mlflow

best = mlflow.search_runs(
    experiment_names=["trip-duration"],
    order_by=["metrics.mae ASC"],
    max_results=1,
).iloc[0]
print(best["tags.mlflow.runName"], best["metrics.mae"])

version = mlflow.register_model(f"runs:/{best.run_id}/model", "trip-duration")
print("version", version.version)

client = mlflow.MlflowClient()
client.set_registered_model_alias("trip-duration", "champion", version.version)
```

```bash
python register.py
```

```
Successfully registered model 'trip-duration'.
Created version '1' of model 'trip-duration'.
rf-depth-20 3.319029923858316
version 1
```

The alias `champion` points to version 1. In the UI, open **Models** and click
on `trip-duration`: version 1, with its alias and the run it came from.

### Load it by name

Create a file `predict.py`. It does not know which run, which parameters or
which library: it asks for `trip-duration@champion`:

```python
import mlflow
import pandas as pd

model = mlflow.pyfunc.load_model("models:/trip-duration@champion")

trips = pd.DataFrame({
    "trip_distance": [1.0, 10.0],
    "pickup_hour": [8.0, 3.0],
    "pickup_weekday": [0.0, 6.0],
    "PULocationID": [161.0, 132.0],
    "DOLocationID": [237.0, 230.0],
})
print(model.predict(trips))
```

```bash
python predict.py
```

```
[ 8.8166715  22.70563524]
```

A one mile trip on a Monday at 8am: 9 minutes. Ten miles on a Sunday at 3am:
23 minutes.

### Serve it

MLflow can serve the model as a REST API, without writing any web code:

```bash
mlflow models serve -m "models:/trip-duration@champion" \
  -p 5002 --env-manager local
```

`--env-manager local` uses the libraries of your virtual environment. Without
it, MLflow creates a new environment from the model's `requirements.txt`.

Wait for `Uvicorn running on http://127.0.0.1:5002`. In another terminal, ask
for the same two predictions:

```bash
curl -X POST http://localhost:5002/invocations \
  -H "Content-Type: application/json" \
  -d '{"dataframe_records": [
        {"trip_distance": 1.0, "pickup_hour": 8, "pickup_weekday": 0,
         "PULocationID": 161, "DOLocationID": 237},
        {"trip_distance": 10.0, "pickup_hour": 3, "pickup_weekday": 6,
         "PULocationID": 132, "DOLocationID": 230}]}'
```

```json
{"predictions": [8.816671500721501, 22.705635238095233]}
```

### A new champion

`rf-depth-20` is 30 times bigger than `rf-depth-10` for 7 seconds less error.
Promote `rf-depth-10` instead. Create a file `promote.py`:

```python
import mlflow

run = mlflow.search_runs(
    experiment_names=["trip-duration"],
    filter_string="params.max_depth = '10' and params.n_estimators = '50'",
    max_results=1,
).iloc[0]

version = mlflow.register_model(f"runs:/{run.run_id}/model", "trip-duration")
print("version", version.version)

client = mlflow.MlflowClient()
client.set_registered_model_alias("trip-duration", "champion", version.version)
```

```bash
python promote.py
```

```
Registered model 'trip-duration' already exists. Creating a new version of this model...
Created version '2' of model 'trip-duration'.
version 2
```

In the UI, `champion` has moved to version 2. Stop `mlflow models serve` with
`Ctrl+C`, start it again with the same command, and send the same `curl`. The
predictions change a little: same command, same URL, a new model:

```json
{"predictions": [8.435981531225003, 23.328249313377015]}
```

### Open a pull request

```bash
git add register.py predict.py promote.py
git commit -m "Register, load and serve the trip duration model"
git push -u origin register-model
```

Open a pull request and merge it when the checks are green.

Questions:

- The new champion is worse in production. How do you go back to version 1?
  How long does it take?
- An app calls `/invocations`. What does it need to change when you promote a
  new model?

## Exercise 5: version the data with DVC (if time allows)

If there is no time in class, do it at home.

Git is not for data, so `data/` is in `.gitignore`. But then nothing records
which version of `trips.parquet` a model was trained on.
[DVC](https://dvc.org/) keeps the data in a bucket and a small `.dvc` file in
Git, with the hash of the data.

```bash
git checkout main
git pull
git checkout -b dvc
```

### Install and initialize

Add `dvc[s3]` to `requirements.txt`, install it, and initialize DVC in the
repository:

```bash
pip install -r requirements.txt
dvc init
```

`dvc init` creates a `.dvc/` folder with its configuration.

### Track the data

DVC writes `data/trips.parquet.dvc` next to the data, and Git has to see that
file. DVC refuses to work inside a folder Git ignores, so `data/` cannot stay
in `.gitignore`. Replace the `data/` line with the other data files, the ones
DVC does not track:

```
data/*.csv
data/*.json
data/yellow_tripdata_*
```

Then track the Parquet file:

```bash
dvc add data/trips.parquet
cat data/trips.parquet.dvc
```

```yaml
outs:
- md5: 3fbbab2b8949308a27b6285f36aae825
  size: 60840464
  hash: md5
  path: trips.parquet
```

The `.dvc` file has the hash (`md5`), the size and the path of the data. That
is what goes to Git. DVC also creates `data/.gitignore`, so Git ignores
`trips.parquet` itself. Check with `git status`: you should see the `.dvc`
file, not the data.

### Push the data to a bucket

In the RustFS console, create a bucket called `dvc`. Add it as the default
remote:

```bash
dvc remote add -d storage s3://dvc
dvc remote modify storage endpointurl http://localhost:9000
dvc remote modify --local storage access_key_id student
dvc remote modify --local storage secret_access_key student-secret
```

`--local` writes the credentials to `.dvc/config.local`, which DVC keeps out
of Git. The rest goes to `.dvc/config`, which you commit.

```bash
dvc push
```

```
1 file pushed
```

Open the `dvc` bucket in the RustFS console: the file is under
`files/md5/3f/`, named by its hash.

### Get it back

```bash
rm data/trips.parquet
dvc pull
ls -la data/
```

### Open a pull request

```bash
git add requirements.txt .gitignore .dvcignore .dvc/config .dvc/.gitignore \
  data/.gitignore data/trips.parquet.dvc
git commit -m "Track the trips data with DVC"
git push -u origin dvc
```

Open a pull request and merge it when the checks are green.

Questions:

- A teammate clones the repository. What do they run to get the same data?
  Which credentials do they need?
- You download February and overwrite `data/trips.parquet`. What do you run so
  Git records the new version? How do you go back to January?
