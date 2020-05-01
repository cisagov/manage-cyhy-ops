"""Provide an interface to manage operator information in SSM."""

SSM_SSH_KEY_PREFIX = "/test//ssh/public_keys/"
SSM_CYHY_OPS_USERNAMES = "/test/cyhy/ops/users"


class ManageOperators:
    """Provide a manager for CyHy Operators.

    This class handles adding, listing, and removing Cyhy Operators from AWS's
    SSM Parameter Store.
    """

    def __init__(self, regions):
        """Set up an operator manager."""
        # Do initialization.
        return

    def update_cyhy_ops_users(self, username: str, remove: bool = False):
        """Update the list of CyHy Operators to use when an instance is built."""
        # Retrieve existing operators.
        # Add user to list.
        # Update parameter in SSM.
        return

    def add_user(self, username, ssh_key: str):
        """Add an Operator to the Parameter Store."""
        # Add user's ssh ssh_key to SSM.
        # Append user to list of operators.
        return

    def remove_user(self, username: str, full: bool = False):
        """Remove an Operator from the Parameter Store."""
        # Remove user from operator list.
        # If --full, then also delete the ssh key parameter.
        return

    def check_user(self, username: str):
        """Check for the existence of an Operator and return information."""
        # Check if the user's key exists.
        # Check if user in list of operators.
        return
