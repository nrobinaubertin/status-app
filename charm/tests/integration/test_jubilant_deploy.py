import contextlib
import json
import os
import pathlib
import shutil
import subprocess

import jubilant
import pytest

APP_NAME = "status-app"
APP_PORT = 8000
RESOURCE_NAME = "flask-app-image"


def _ensure_juju_available() -> None:
    try:
        subprocess.run(
            ["juju", "whoami"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        pytest.skip(f"Juju not available: {exc}")


def _resolve_path(path: str, repo_root: pathlib.Path) -> pathlib.Path:
    candidate = pathlib.Path(path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve()


def _build_charm(charm_root: pathlib.Path, pytestconfig: pytest.Config) -> pathlib.Path:
    repo_root = charm_root.parent
    charm_file = pytestconfig.getoption("--charm-file")
    if charm_file:
        return _resolve_path(charm_file, repo_root)

    charm_file = os.environ.get("STATUS_APP_CHARM_FILE")
    if charm_file:
        return _resolve_path(charm_file, repo_root)

    if os.environ.get("STATUS_APP_BUILD_ARTIFACTS") != "1":
        pytest.skip(
            "Set --charm-file, STATUS_APP_CHARM_FILE, or STATUS_APP_BUILD_ARTIFACTS=1 "
            "to build the charm"
        )

    if not shutil.which("charmcraft"):
        pytest.skip("charmcraft not available; set STATUS_APP_CHARM_FILE to a packed charm")

    subprocess.run(["charmcraft", "pack"], cwd=charm_root, check=True, text=True)
    candidates = sorted(charm_root.glob(f"{APP_NAME}_*.charm"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        pytest.skip("No packed charm found after running charmcraft pack")
    return candidates[-1]


def _rock_image_from_config(pytestconfig: pytest.Config) -> str | None:
    return pytestconfig.getoption("--rock-image") or os.environ.get("STATUS_APP_ROCK_IMAGE")


def _juju_context(pytestconfig: pytest.Config) -> contextlib.AbstractContextManager[jubilant.Juju]:
    use_existing = pytestconfig.getoption("--use-existing")
    if use_existing:
        return contextlib.nullcontext(jubilant.Juju())

    model = pytestconfig.getoption("--model")
    if model:
        return contextlib.nullcontext(jubilant.Juju(model=model))

    keep_models = pytestconfig.getoption("--keep-models")
    return jubilant.temp_model(keep=keep_models)


@pytest.mark.integration
def test_deploy_and_fetch_output(pytestconfig: pytest.Config):
    _ensure_juju_available()

    repo_root = pathlib.Path(__file__).resolve().parents[3]
    charm_root = repo_root / "charm"

    use_existing = pytestconfig.getoption("--use-existing")
    charm_file = None
    rock_image = _rock_image_from_config(pytestconfig)
    if not use_existing:
        charm_file = _build_charm(charm_root, pytestconfig)
        if not rock_image:
            pytest.skip("Set --rock-image or STATUS_APP_ROCK_IMAGE to deploy the rock image")

    with _juju_context(pytestconfig) as juju:
        juju.wait_timeout = 900
        if not use_existing:
            juju.deploy(
                str(charm_file),
                app=APP_NAME,
                resources={RESOURCE_NAME: rock_image},
            )
            juju.wait(jubilant.all_active)

        task = juju.exec(
            "python3",
            "-c",
            (
                "import json, urllib.request; "
                f"data=urllib.request.urlopen('http://localhost:{APP_PORT}/').read(); "
                "print(data.decode())"
            ),
            unit=f"{APP_NAME}/0",
        )

        payload = json.loads(task.stdout.strip())
        assert "server" in payload
        assert "request" in payload
