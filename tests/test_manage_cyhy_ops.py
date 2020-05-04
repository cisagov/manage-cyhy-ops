"""Tests for manage_cyhy_ops."""

# Standard Python Libraries
import os
import sys
from unittest.mock import patch

# Third-Party Libraries
import pytest

# cisagov Libraries
import manage_cyhy_ops

# Define sources of version strings.
RELEASE_TAG = os.getenv("RELEASE_TAG")
PROJECT_VERSION = manage_cyhy_ops.__version__


def test_stdout_version(capsys):
    """Verify that version string sent to stdout agrees with the module version."""
    with pytest.raises(SystemExit):
        with patch.object(sys, "argv", ["bogus", "--version"]):
            manage_cyhy_ops.cli.main()
        captured = capsys.readouterr()
        assert (
            captured.out == f"{PROJECT_VERSION}\n"
        ), "Standard output by '--version' should agree with module.__version__"


@pytest.mark.skipif(
    RELEASE_TAG in [None, ""], reason="This is not a release (RELEASE_TAG not set)."
)
def test_release_version():
    """Verify that release tag version agrees with the module version."""
    assert (
        RELEASE_TAG == f"v{PROJECT_VERSION}"
    ), "RELEASE_TAG does not match the project version."
