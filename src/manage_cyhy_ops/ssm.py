"""Provide an interface to manage operator information in SSM."""

# Standard Python Libraries
import logging
from typing import Dict, List

# Third-Party Libraries
import boto3
from botocore.exceptions import ClientError

SSM_SSH_KEY_PREFIX = "/test/ssh/public_keys/"
SSM_CYHY_OPS_USERNAMES = "/test/cyhy/ops/users"


class ManageOperators:
    """Provide a manager for CyHy Operators.

    This class handles adding, listing, and removing Cyhy Operators from AWS's
    SSM Parameter Store.
    """

    def __init__(self, regions: List):
        """Set up an operator manager."""
        self.clients: Dict = {}
        for region in regions:
            try:
                self.clients[region] = boto3.client("ssm", region_name=region)
            except ClientError as e:
                logging.error(f"Unable to setup SSM client in region {region}.")
                raise e

    def update_cyhy_ops_users(self, username: str, region: str, remove: bool = False):
        """Update the list of CyHy Operators to use when an instance is built."""
        client = self.clients[region]

        users: List = []
        try:
            response = client.get_parameter(
                Name=SSM_CYHY_OPS_USERNAMES, WithDecryption=True
            )
            users = response["Parameter"]["Value"].split(",")
        except client.exceptions.ParameterNotFound:
            logging.warning(
                f'The CyHy Operators parameter "{SSM_CYHY_OPS_USERNAMES}" '
                f'does not exist in region "{region}".'
            )

        logging.debug("Current CyHy Operators: {users}.")

        if remove:
            if username not in users:
                logging.warning(
                    f'User "{username}" is not in the list of active CyHy Operators.'
                )
            else:
                users.remove(username)
        else:
            if username in users:
                logging.warning(
                    f'User "{username}" is already in the list of active '
                    "CyHy Operators."
                )
            else:
                users.append(username)

        if len(users) == 0:
            try:
                logging.warning(
                    "No CyHy Operators left, deleting parameter "
                    f'from region "{region}".'
                )
                # Response is an empty dictionary on success.
                client.delete_parameter(Name=SSM_CYHY_OPS_USERNAMES)
            except ClientError as e:
                logging.error(e)
        else:
            updated_users = ",".join(users)

            logging.debug(f'New CyHy Operators value: "{updated_users}".')

            try:
                # The SSM response on success currently only contains a version
                # number and the parameter tier.
                # Neither are useful to us at this time, so we don't store them..
                client.put_parameter(
                    Name=SSM_CYHY_OPS_USERNAMES,
                    Value=updated_users,
                    Type="SecureString",
                    Overwrite=True,
                )
                logging.info(f'Successfully updated CyHy Operators in "{region}".')
            except Exception as e:
                logging.warning(
                    f'Unable to update parameter "{SSM_CYHY_OPS_USERNAMES}" '
                    f'in region "{region}".'
                )
                logging.warning(e)

    def add_user(self, username: str, ssh_key: str, overwrite: bool = False):
        """Add an Operator to the Parameter Store."""
        # Should this be atomic?
        for region, client in self.clients.items():
            try:
                # The SSM response on success currently only contains a version
                # number and the parameter tier.
                # Neither are useful to us at this time, so we don't store them..
                logging.debug(
                    f'Adding SSH key to Parameter Store in "{region}" with key '
                    f'"{SSM_SSH_KEY_PREFIX}{username}".'
                )
                client.put_parameter(
                    Name=f"{SSM_SSH_KEY_PREFIX}{username}",
                    Value=ssh_key,
                    Type="SecureString",
                    Overwrite=overwrite,
                )
                logging.info(
                    f'Successfully added "{username}"\'s SSH key to the '
                    f'Parameter Store in "{region}".'
                )
            except client.exceptions.ParameterAlreadyExists:
                logging.warning(
                    f'SSH key for "{username}" already exists in the '
                    f'Parameter Store for region "{region}".'
                )
                logging.warning(
                    "If you need to overwrite this value, please use the "
                    '"--overwrite" switch.'
                )
            except ClientError as e:
                logging.error(e)

            self.update_cyhy_ops_users(username, region)

    def remove_user(self, username: str, full: bool = False):
        """Remove an Operator from the Parameter Store."""
        # Should this be atomic?
        for region, client in self.clients.items():
            if full:
                try:
                    parameter_name = f"{SSM_SSH_KEY_PREFIX}{username}"
                    # Response is an empty dictionary on success.
                    client.delete_parameter(Name=parameter_name)
                except client.exceptions.ParameterNotFound:
                    logging.warning(
                        f'User "{username}" dot not have an SSH key stored in '
                        f'the Parameter Store of region "{region}".'
                    )
                except ClientError as e:
                    logging.error(e)
            self.update_cyhy_ops_users(username, region, remove=True)
            logging.info(
                f'Successfully removed "{username}" from CyHy Operators '
                f'in region "{region}".'
            )

    def check_user(self, username: str):
        """Check for the existence of an Operator and return information."""
        for region, client in self.clients.items():
            try:
                response = client.get_parameter(
                    Name=f"{SSM_SSH_KEY_PREFIX}{username}", WithDecryption=True
                )
                logging.info(
                    f'User "{username}" has the following SSH key in the '
                    f'Parameter Store of region "{region}":'
                )
                logging.info(response["Parameter"]["Value"])
            except client.exceptions.ParameterNotFound:
                logging.info(
                    f'User "{username}" does not have an SSH key in the '
                    f'Parameter Store of region "{region}".'
                )
            except ClientError as e:
                logging.error(e)
            try:
                response = client.get_parameter(
                    Name=SSM_CYHY_OPS_USERNAMES, WithDecryption=True
                )
                enabled_users = response["Parameter"]["Value"].split(",")
                if username in enabled_users:
                    user_status = "is set"
                else:
                    user_status = "is not set"
                logging.info(
                    f'User "{username}" {user_status} as a CyHy Operator '
                    f'in region "{region}".'
                )
            except client.exceptions.ParameterNotFound:
                logging.warning(
                    f'The CyHy Operators parameter "{SSM_CYHY_OPS_USERNAMES}" '
                    f'does not exist in region "{region}".'
                )
