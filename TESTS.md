# Integration tests

This document explains how to run the charm integration tests using a packed
charm (`*.charm`) and a rock image loaded into a registry.

## Prerequisites

- A Juju controller backed by a Kubernetes cloud (MicroK8s is a common choice).
- `rockcraft`, `charmcraft`, and `tox` installed.
- `rockcraft.skopeo` (from the rockcraft snap) or `skopeo` available.
- A reachable OCI registry for the rock image (MicroK8s registry is a common choice).

## Build the artifacts

```
make pack
```

This creates:

- `status-app_*.rock` in the repository root.
- `charm/status-app_*.charm` in the `charm/` directory.

## Load the rock into a registry

Run `make pack` to create the rock, then push it to your registry. For the
MicroK8s registry, push the rock with `skopeo` (or `rockcraft.skopeo` if you
installed rockcraft via snap):

```
skopeo --insecure-policy copy --dest-tls-verify=false \
  oci-archive:./status-app_0.1_amd64.rock \
  docker://localhost:32000/status-app:0.1
```

Verify the registry is reachable:

```
curl -fsS http://localhost:32000/v2/
```

## Run integration tests with the packed artifacts

Point the tests at the charm and the registry image:

```
make integration \
  STATUS_APP_CHARM_FILE=./charm/status-app_ubuntu@24.04-amd64.charm \
  STATUS_APP_ROCK_IMAGE=localhost:32000/status-app:0.1
```

If you want to invoke tox directly, use pytest options:

```
tox -e charm-integration -- \
  --charm-file=./charm/status-app_ubuntu@24.04-amd64.charm \
  --rock-image=localhost:32000/status-app:0.1
```

## Optional pytest flags

- `--use-existing`: reuse an existing deployment (skips deploy).
- `--model <name>`: run against a specific Juju model.
- `--keep-models`: keep any temporary models created for the test.
