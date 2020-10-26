# manage-cyhy-ops #

[![GitHub Build Status](https://github.com/cisagov/manage-cyhy-ops/workflows/build/badge.svg)](https://github.com/cisagov/manage-cyhy-ops/actions)
[![Coverage Status](https://coveralls.io/repos/github/cisagov/manage-cyhy-ops/badge.svg?branch=develop)](https://coveralls.io/github/cisagov/manage-cyhy-ops?branch=develop)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/cisagov/manage-cyhy-ops.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/cisagov/manage-cyhy-ops/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/cisagov/manage-cyhy-ops.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/cisagov/manage-cyhy-ops/context:python)
[![Known Vulnerabilities](https://snyk.io/test/github/cisagov/manage-cyhy-ops/develop/badge.svg)](https://snyk.io/test/github/cisagov/manage-cyhy-ops)

This is a Python package to manage the list of SSH users to add to a system
using the
[AWS Systems Manager's Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/features.html#parameter-store)
. This is used by
[cisagov/ansible-role-dev-ssh-access](https://github.com/cisagov/ansible-role-dev-ssh-access)
and in [cisagov/cyhy_amis](https://github.com/cisagov/cyhy_amis) in the
[cyhy_ops Ansible role](https://github.com/cisagov/cyhy_amis/blob/develop/ansible/roles/cyhy_ops)
.

## Contributing ##

We welcome contributions!  Please see [`CONTRIBUTING.md`](CONTRIBUTING.md) for
details.

## License ##

This project is in the worldwide [public domain](LICENSE).

This project is in the public domain within the United States, and
copyright and related rights in the work worldwide are waived through
the [CC0 1.0 Universal public domain
dedication](https://creativecommons.org/publicdomain/zero/1.0/).

All contributions to this project will be released under the CC0
dedication. By submitting a pull request, you are agreeing to comply
with this waiver of copyright interest.
