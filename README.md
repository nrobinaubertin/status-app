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

Run charm integration tests (requires Juju and a Kubernetes controller):

```
make integration
```

The jubilant deploy test expects either prebuilt artifacts or explicit build
opt-in. The Makefile wires these options through:

- `STATUS_APP_CHARM_FILE`: path to a packed charm (`*.charm`).
- `STATUS_APP_ROCK_IMAGE`: registry reference for the rock image.
- `STATUS_APP_BUILD_ARTIFACTS=1`: allow the test to build both artifacts.

After running `make pack`, load the rock into your registry and then run the
tests, for example:

```
make integration STATUS_APP_CHARM_FILE=./charm/status-app_0.1_amd64.charm STATUS_APP_ROCK_IMAGE=localhost:32000/status-app:0.1
```

You can also pass explicit artifacts via pytest options when invoking tox
directly:

```
tox -e charm-integration -- --charm-file=./charm/status-app_0.1_amd64.charm --rock-image=localhost:32000/status-app:0.1
```

Load the rock into your registry before running the tests. For MicroK8s with
the registry addon enabled, you can push the rock with `skopeo` (or
`rockcraft.skopeo` if you installed rockcraft via snap):

```
skopeo --insecure-policy copy --dest-tls-verify=false \
  oci-archive:./status-app_0.1_amd64.rock \
  docker://localhost:32000/status-app:0.1
```

Verify the registry is reachable before running the tests:

```
curl -fsS http://localhost:32000/v2/
```

Other integration test options:

- `--use-existing`: reuse an existing deployment (skips deploy).
- `--model <name>`: run against a specific Juju model (no temp model).
- `--keep-models`: keep any temporary models created for the test.
- `--rock-image <ref>`: registry reference for the rock image.

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
