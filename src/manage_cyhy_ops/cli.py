"""Manage CyHy operator data SSM parameters.

Usage:
  manage-cyhy-ops [--debug] [--regions=REGIONS] [--ssm-cyhy-ops=CYHY_OPS]
    [--ssm-ssh-prefix=SSH_PREFIX] add [--overwrite] [--username=USERNAME] SSH_KEY
  manage-cyhy-ops [--debug] [--regions=REGIONS] [--ssm-cyhy-ops=CYHY_OPS]
    [--ssm-ssh-prefix=SSH_PREFIX] remove [--full] USERNAME
  manage-cyhy-ops [--debug] [--regions=REGIONS] [--ssm-cyhy-ops=CYHY_OPS]
    [--ssm-ssh-prefix=SSH_PREFIX] list USERNAME
  manage-cyhy-ops (-h | --help)
  manage-cyhy-ops --version

Arguments:
  SSH_KEY   An SSH key in the format "ssh-ed25519 <SSH key> <comment>".
            Note: If a username is not provided with --username, then the
            SSH key comment should be a username in the format "firstname.lastname".
  USERNAME  A username in the format "firstname.lastname".

Options:
  -h --help                    Show this message.
  --version                    Show version.
  --debug                      Enable debug messages.
  --regions=REGIONS            Comma delimited list of AWS regions to use.
                               [default: us-east-1,us-east-2,us-west-1,us-west-2]
  --ssm-cyhy-ops=CYHY_OPS      The key that is used in the Parameter Store for
                               the list of active CyHy Operators.
                               [default: /cyhy/ops/users]
  --ssm-ssh-prefix=SSH_PREFIX  The prefix to use when working with SSH keys
                               stored in the Parameter Store.
                               [default: /ssh/public_keys]
  --overwrite                  Overwrite the user's SSH key if one already exists.
  --full                       Also remove the user's SSH key from SSM.
"""

# Standard Python Libraries
import logging
import sys
from typing import Any, Dict, List

# Third-Party Libraries
import docopt
from schema import And, Or, Regex, Schema, SchemaError, Use

from ._version import __version__
from .manageoperators import ManageOperators

ALLOWED_REGIONS = ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]
# AWS only allows these characters in Parameter Store keys.
VALID_SSM_CHARS = r"^[a-zA-Z0-9.\-_/]*$"
# Subset of valid characters we'll allow for usernames.
VALID_USERNAME = r"^[a-zA-Z0-9.\-_]*$"
USERNAME_ERROR_MSG = (
    'Username must be in the format "firstname.lastname", and can only consist '
    'of letters, numbers, and the characters ".-_".'
)
# The Schema for an SSM key is used more than once so we define it here.
SSM_KEY_VALIDATE = And(
    str,
    Use(str.lower),
    Regex(VALID_SSM_CHARS),
    lambda s: s[0] == "/" if "/" in s else True,
    error="Invalid SSM key provided.",
)
# The Schema for a username is used in multiple places so we define it here.
USERNAME_VALIDATE = Or(
    None,
    And(
        str,
        Use(str.lower),
        Regex(VALID_USERNAME),
        lambda s: len(s.split(".")) >= 2,
        error=f"USER {USERNAME_ERROR_MSG}",
    ),
)


def main() -> int:
    """Provide an interface to manage CyHy operators."""
    args: Dict[str, str] = docopt.docopt(__doc__, version=__version__)

    schema: Schema = Schema(
        {
            "--regions": And(
                str,
                lambda s: False
                if False in map(lambda e: e in ALLOWED_REGIONS, s.split(","))
                else True,
                error=f"Invalid region(s) provided. Valid regions are: {ALLOWED_REGIONS}",
            ),
            "--ssm-ssh-prefix": SSM_KEY_VALIDATE,
            "--ssm-cyhy-ops": SSM_KEY_VALIDATE,
            "--username": USERNAME_VALIDATE,
            "SSH_KEY": Or(
                None,
                And(
                    str,
                    lambda s: len(s.split(" ")) == 3,
                    error="Invalid SSH key format.",
                ),
            ),
            "USERNAME": USERNAME_VALIDATE,
            str: object,  # No other validation to perform.
        }
    )

    try:
        validated_args: Dict[str, Any] = schema.validate(args)
    except SchemaError as err:
        # Exit because one or more of the arguments were invalid.
        print(err, file=sys.stderr)
        return 1

    # Set up logging.
    log_level: str = "DEBUG" if validated_args["--debug"] else "INFO"
    logging.basicConfig(
        format="%(asctime)-15s %(levelname)s %(message)s", level=log_level
    )

    logging.debug(validated_args)

    try:
        regions: List = validated_args["--regions"].split(",")
        cyhy_ops: str = validated_args["--ssm-cyhy-ops"]
        ssh_prefix: str = validated_args["--ssm-ssh-prefix"]
        managers: List[ManageOperators] = []
        for region in regions:
            managers.append(ManageOperators(region, cyhy_ops, ssh_prefix))
    except Exception as e:
        logging.error(e)
        return 1

    username = validated_args["USERNAME"]
    overwrite_ssh_key = validated_args["--overwrite"]
    delete_ssh_key = validated_args["--full"]

    results: List[int] = []
    if validated_args["add"]:
        ssh_key: str = validated_args["SSH_KEY"]

        if validated_args["--username"]:
            username = validated_args["--username"]
        else:
            logging.debug("Using SSH key comment as username.")
            try:
                username = Schema(USERNAME_VALIDATE).validate(ssh_key.split(" ")[2])
            except SchemaError as err:
                logging.error(err)
                return 1

        for manager in managers:
            results.append(
                manager.add_user(username, ssh_key, overwrite=overwrite_ssh_key)
            )
    elif validated_args["remove"]:
        for manager in managers:
            results.append(manager.remove_user(username, delete_ssh_key))
    elif validated_args["list"]:
        for manager in managers:
            results.append(manager.check_user(username))
    else:
        logging.info("Feature not implemented yet.")

    # Right now all return statuses from the Manager are 1, but that is not
    # guaranteed in the future. This handles any non-successful error code.
    if True in map(lambda e: e != 0, results):
        return 1
    else:
        return 0
