import json
import os
import pathlib
import shutil
import subprocess

import jubilant
import pytest

APP_NAME = "status-app"
APP_PORT = 8080


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


def _build_charm(charm_root: pathlib.Path) -> pathlib.Path:
    charm_file = os.environ.get("STATUS_APP_CHARM_FILE")
    if charm_file:
        return pathlib.Path(charm_file).resolve()

    if os.environ.get("STATUS_APP_BUILD_ARTIFACTS") != "1":
        pytest.skip(
            "Set STATUS_APP_CHARM_FILE or STATUS_APP_BUILD_ARTIFACTS=1 to build the charm"
        )

    if not shutil.which("charmcraft"):
        pytest.skip("charmcraft not available; set STATUS_APP_CHARM_FILE to a packed charm")

    subprocess.run(["charmcraft", "pack"], cwd=charm_root, check=True, text=True)
    candidates = sorted(charm_root.glob(f"{APP_NAME}_*.charm"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        pytest.skip("No packed charm found after running charmcraft pack")
    return candidates[-1]


def _build_rock(repo_root: pathlib.Path) -> pathlib.Path:
    rock_file = os.environ.get("STATUS_APP_ROCK_FILE")
    if rock_file:
        return pathlib.Path(rock_file).resolve()

    if os.environ.get("STATUS_APP_BUILD_ARTIFACTS") != "1":
        pytest.skip(
            "Set STATUS_APP_ROCK_FILE or STATUS_APP_BUILD_ARTIFACTS=1 to build the rock"
        )

    if not shutil.which("rockcraft"):
        pytest.skip("rockcraft not available; set STATUS_APP_ROCK_FILE to a packed rock")

    subprocess.run(["rockcraft", "pack"], cwd=repo_root, check=True, text=True)
    candidates = sorted(repo_root.glob(f"{APP_NAME}_*.rock"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        pytest.skip("No packed rock found after running rockcraft pack")
    return candidates[-1]


@pytest.mark.integration
def test_deploy_and_fetch_output():
    _ensure_juju_available()

    repo_root = pathlib.Path(__file__).resolve().parents[3]
    charm_root = repo_root / "charm"

    charm_file = _build_charm(charm_root)
    rock_file = _build_rock(repo_root)

    with jubilant.temp_model() as juju:
        juju.wait_timeout = 900
        juju.deploy(
            str(charm_file),
            app=APP_NAME,
            resources={"app-image": str(rock_file)},
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
