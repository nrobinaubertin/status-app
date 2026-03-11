"""Module for test customizations."""


def _addoption(parser, *args, **kwargs):
    """Register an option unless a plugin already added it."""
    try:
        parser.addoption(*args, **kwargs)
    except ValueError as exc:
        if "already added" not in str(exc):
            raise


def pytest_addoption(parser):
    """Adds parser switches."""
    _addoption(parser, "--charm-file", action="store", default=None)
    _addoption(
        parser,
        "--rock-image",
        action="store",
        default=None,
        help="Registry reference to use for the rock image.",
    )
    _addoption(
        parser,
        "--use-existing",
        action="store_true",
        default=False,
        help="Skip deploying the charm, using an existing deployment instead.",
    )
    _addoption(
        parser,
        "--keep-models",
        action="store_true",
        default=False,
        help="Keep temporarily-created models.",
    )
    _addoption(
        parser,
        "--model",
        action="store",
        help=(
            "Juju model to use; if not provided, a new model will be created for each "
            "test which requires one."
        ),
    )
