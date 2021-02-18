"""Provide an interface to manage operator information in SSM."""

# Standard Python Libraries
import logging
from typing import List

# Third-Party Libraries
import boto3
from botocore.exceptions import ClientError


class ManageOperators:
    """Manage CyHy operators in a given AWS region.

    This class handles adding, listing, and removing Cyhy Operators from AWS's
    SSM Parameter Store in a specified region.
    """

    def __init__(self, region: str, cyhy_ops_key: str, ssh_key_prefix: str):
        """Set up an operator manager."""
        self.cyhy_ops_key = cyhy_ops_key
        self.ssh_key_prefix = ssh_key_prefix
        self.region = region
        try:
            self._client = boto3.client("ssm", region_name=region)
        except ClientError as e:
            logging.error(f'Unable to setup SSM client in region "{region}".')
            raise e

    def _get_cyhy_ops_list(self) -> List[str]:
        users: List[str] = []
        try:
            response = self._client.get_parameter(
                Name=self.cyhy_ops_key, WithDecryption=True
            )
            users = response.get("Parameter", {}).get("Value", "").split(",")
        except self._client.exceptions.ParameterNotFound:
            logging.warning(
                f'The CyHy Operators parameter "{self.cyhy_ops_key}" '
                f'does not exist in region "{self.region}".'
            )
        except ClientError as e:
            logging.error(e)

        return users

    def _update_cyhy_ops_users(self, username: str, remove: bool = False) -> int:
        """Update the list of CyHy Operators to use when an instance is built."""
        users: List[str] = self._get_cyhy_ops_list()
        update_msg: str = "performed no operations on"

        logging.debug("Current CyHy Operators: {users}.")

        if remove:
            if username not in users:
                logging.warning(
                    f'User "{username}" is not in the list of active '
                    f'CyHy Operators in region "{self.region}".'
                )
            else:
                users.remove(username)
                update_msg = f'removed "{username}" from'
        else:
            if username in users:
                logging.warning(
                    f'User "{username}" is already in the list of active '
                    f'CyHy Operators in region "{self.region}".'
                )
            else:
                users.append(username)
                update_msg = f'added "{username}" to'

        updated_users = ",".join(sorted(users))

        logging.debug(f'New CyHy Operators value: "{updated_users}".')

        try:
            # The SSM response on success currently only contains a version
            # number and the parameter tier.
            # Neither are useful to us at this time, so we don't store them..
            self._client.put_parameter(
                Name=self.cyhy_ops_key,
                Value=updated_users,
                Type="SecureString",
                Overwrite=True,
            )
            logging.info(
                f"Successfully {update_msg} CyHy Operators in region "
                f'"{self.region}".'
            )
        except ClientError as e:
            logging.error(
                f'Unable to update parameter "{self.cyhy_ops_key}" '
                f'in region "{self.region}".'
            )
            logging.error(e)
            return 1

        return 0

    def add_user(self, username: str, ssh_key: str, overwrite: bool = False) -> int:
        """Add an Operator to the Parameter Store."""
        # Should this be atomic?
        try:
            # The SSM response on success currently only contains a version
            # number and the parameter tier.
            # Neither are useful to us at this time, so we don't store them..
            logging.debug(
                f'Adding SSH key to Parameter Store in "{self.region}" with key '
                f'"{self.ssh_key_prefix}/{username}".'
            )
            self._client.put_parameter(
                Name=f"{self.ssh_key_prefix}/{username}",
                Value=ssh_key,
                Type="SecureString",
                Overwrite=overwrite,
            )
            logging.info(
                f'Successfully added "{username}"\'s SSH key to the '
                f'Parameter Store in "{self.region}".'
            )
        except self._client.exceptions.ParameterAlreadyExists:
            logging.warning(
                f'SSH key for "{username}" already exists in the '
                f'Parameter Store for region "{self.region}".'
            )
            logging.warning(
                "If you need to overwrite this value, please use the "
                '"--overwrite" switch.'
            )
        except ClientError as e:
            logging.error(e)
            return 1

        return self._update_cyhy_ops_users(username)

    def remove_user(self, username: str, full: bool = False) -> int:
        """Remove an Operator from the Parameter Store."""
        # Should this be atomic?
        if full:
            try:
                parameter_name = f"{self.ssh_key_prefix}/{username}"
                # Response is an empty dictionary on success.
                self._client.delete_parameter(Name=parameter_name)
                logging.info(
                    f'Successfully removed SSH key for user "{username}" '
                    f'in region "{self.region}".'
                )
            except self._client.exceptions.ParameterNotFound:
                logging.warning(
                    f'User "{username}" dot not have an SSH key stored in '
                    f'the Parameter Store of region "{self.region}".'
                )
            except ClientError as e:
                logging.error(e)
                return 1

        return self._update_cyhy_ops_users(username, remove=True)

    def check_user(self, username: str) -> int:
        """Check for the existence of an Operator and return information."""
        try:
            response = self._client.get_parameter(
                Name=f"{self.ssh_key_prefix}/{username}", WithDecryption=True
            )
            logging.info(
                f'User "{username}" has the following SSH key in the '
                f'Parameter Store of region "{self.region}":'
            )
            logging.info(response["Parameter"]["Value"])
        except self._client.exceptions.ParameterNotFound:
            logging.info(
                f'User "{username}" does not have an SSH key in the '
                f'Parameter Store of region "{self.region}".'
            )
        except ClientError as e:
            logging.error(e)
            return 1

        enabled_users: List[str] = self._get_cyhy_ops_list()
        if not enabled_users:
            return 1

        if username in enabled_users:
            user_status = "is set"
        else:
            user_status = "is not set"
        logging.info(
            f'User "{username}" {user_status} as a CyHy Operator '
            f'in region "{self.region}".'
        )

        return 0
