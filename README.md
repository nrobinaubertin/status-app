# Status App

This repository contains a small Flask service that returns system and request
information as JSON, plus a Juju charm for deploying it on Kubernetes via the
`paas-charm` framework.

## Repository layout

- `app.py`: Flask entrypoint for the workload.
- `requirements.txt`: Python dependencies for the workload.
- `rockcraft.yaml`: Rockcraft build definition for the OCI image.
- `charm/`: Charm project (source, config, tests).

## Run the app locally

```
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Then visit `http://localhost:5000/` to see the JSON response.

## Tests

Run the workload unit tests:

```
tox -e unit
```

Run charm linting:

```
tox -e lint
```

Run charm integration tests (requires Juju and a controller):

```
tox -e charm-integration
```

The jubilant deploy test expects either prebuilt artifacts or explicit build
opt-in:

- `STATUS_APP_CHARM_FILE`: path to a packed charm (`*.charm`).
- `STATUS_APP_ROCK_FILE`: path to a packed rock (`*.rock`).
- `STATUS_APP_BUILD_ARTIFACTS=1`: allow the test to build both artifacts.

## Build artifacts

Build the OCI rock:

```
rockcraft pack
```

Build the charm:

```
cd charm
charmcraft pack
```
