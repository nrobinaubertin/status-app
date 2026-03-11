import jubilant
import pytest


@pytest.mark.integration
def test_temp_model_status():
    with jubilant.temp_model() as juju:
        status = juju.status()
        assert status
