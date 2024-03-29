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
        except ClientError as err:
            logging.error('Unable to setup SSM client in region "%s".', region)
            raise err

    def _get_cyhy_ops_list(self) -> List[str]:
        users: List[str] = []
        try:
            response = self._client.get_parameter(
                Name=self.cyhy_ops_key, WithDecryption=True
            )
            users = response.get("Parameter", {}).get("Value", "").split(",")
        except self._client.exceptions.ParameterNotFound:
            logging.warning(
                'The CyHy Operators parameter "%s" does not exist in region "%s".',
                self.cyhy_ops_key,
                self.region,
            )
        except ClientError as err:
            logging.error(err)

        return users

    def _update_cyhy_ops_users(self, user: str, remove: bool = False) -> int:
        """Update the list of CyHy Operators to use when an instance is built."""
        users: List[str] = self._get_cyhy_ops_list()
        update_msg: str = 'Performed no operations for "%s"'

        logging.debug("Current CyHy Operators: %s.", users)

        if remove:
            if user not in users:
                logging.warning(
                    'User "%s" is not in the list of active CyHy Operators in region "%s".',
                    user,
                    self.region,
                )
            else:
                users.remove(user)
                update_msg = 'Removed "%s" from Cyhy Operators'
        else:
            if user in users:
                logging.warning(
                    'User "%s" is already in the list of active CyHy Operators in region "%s".',
                    user,
                    self.region,
                )
            else:
                users.append(user)
                update_msg = 'Added "%s" to Cyhy Operators'

        updated_users = ",".join(sorted(users))

        logging.debug('New CyHy Operators value: "%s".', updated_users)

        try:
            # The SSM response on success currently only contains a version
            # number and the parameter tier.
            # Neither are useful to us at this time, so we don't store them.
            self._client.put_parameter(
                Name=self.cyhy_ops_key,
                Value=updated_users,
                Type="SecureString",
                Overwrite=True,
            )
            log_msg = f'{update_msg} in region "%s".'
            logging.info(log_msg, user, self.region)
        except ClientError as err:
            logging.error(
                'Unable to update parameter "%s" in region "%s".',
                self.cyhy_ops_key,
                self.region,
            )
            logging.error(err)
            return 1

        return 0

    def add_user(self, user: str, ssh_key: str, overwrite: bool = False) -> int:
        """Add an Operator to the Parameter Store."""
        # Should this be atomic?
        try:
            # The SSM response on success currently only contains a version
            # number and the parameter tier.
            # Neither are useful to us at this time, so we don't store them.
            logging.debug(
                'Adding SSH key "%s/%s" to the Parameter Store in region "%s".',
                self.ssh_key_prefix,
                user,
                self.region,
            )
            self._client.put_parameter(
                Name=f"{self.ssh_key_prefix}/{user}",
                Value=ssh_key,
                Type="SecureString",
                Overwrite=overwrite,
            )
            logging.info(
                'Added "%s"\'s SSH key to the Parameter Store in "%s".',
                user,
                self.region,
            )
        except self._client.exceptions.ParameterAlreadyExists:
            logging.warning(
                'SSH key for "%s" already exists in the Parameter Store in region "%s".',
                user,
                self.region,
            )
            logging.warning(
                'If you need to overwrite this value, please use the "--overwrite" switch.'
            )
        except ClientError as err:
            logging.error(err)
            return 1

        return self._update_cyhy_ops_users(user)

    def remove_user(self, user: str, full: bool = False) -> int:
        """Remove an Operator from the Parameter Store."""
        # Should this be atomic?
        if full:
            try:
                parameter_name = f"{self.ssh_key_prefix}/{user}"
                # Response is an empty dictionary on success.
                self._client.delete_parameter(Name=parameter_name)
                logging.info(
                    'Removed SSH key for "%s" from the Parameter Store in region "%s".',
                    user,
                    self.region,
                )
            except self._client.exceptions.ParameterNotFound:
                logging.warning(
                    'SSH key for "%s" does not exist in the Parameter Store in region "%s".',
                    user,
                    self.region,
                )
            except ClientError as err:
                logging.error(err)
                return 1

        return self._update_cyhy_ops_users(user, remove=True)

    def check_user(self, user: str) -> int:
        """Check for the existence of an Operator and return information."""
        try:
            response = self._client.get_parameter(
                Name=f"{self.ssh_key_prefix}/{user}", WithDecryption=True
            )
            logging.info(
                'User "%s" has the following SSH key in the Parameter Store of region "%s":',
                user,
                self.region,
            )
            logging.info(response["Parameter"]["Value"])
        except self._client.exceptions.ParameterNotFound:
            logging.info(
                'User "%s" does not have an SSH key in the Parameter Store of region "%s".',
                user,
                self.region,
            )
        except ClientError as err:
            logging.error(err)
            return 1

        enabled_users: List[str] = self._get_cyhy_ops_list()
        if not enabled_users:
            return 1

        log_msg = (
            'User "%s" is '
            + ("" if user in enabled_users else "not ")
            + 'set as a CyHy Operator in region "%s".'
        )
        logging.info(log_msg, user, self.region)

        return 0
