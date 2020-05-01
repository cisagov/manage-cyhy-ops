"""Manage CyHy operator data SSM parameters.

Usage:
  manage-cyhy-ops add [--regions=REGIONS] [--overwrite] <SSH_KEY>...
  manage-cyhy-ops list [--regions=REGIONS] <USERNAME>
  manage-cyhy-ops remove [--regions=REGIONS] [--full] <USERNAME>
  manage-cyhy-ops (-h | --help)
  manage-cyhy-ops --version

Options:
  -h --help    Show this message.
  --version    Show version.
  --regions    Comma delimited list of AWS regions to use
               [default: "us-east-1,us-east-2,us-west-1,us-west2"].
  --overwrite  Overwrite the user's SSH key if one already exists
               [default: False].
  --full       Also remove the user's SSH key from SSM [default: False].
"""


def main() -> int:
    """Provide an interface to manage CyHy operators."""
    # do stuff.
    return 0
