import os

import jubilant
import pytest


@pytest.mark.integration
def test_temp_model_status():
    if "JUJU_MODEL" not in os.environ:
        pytest.skip("JUJU_MODEL not set; requires a Juju controller and model")

    with jubilant.temp_model() as juju:
        status = juju.status()
        assert status
