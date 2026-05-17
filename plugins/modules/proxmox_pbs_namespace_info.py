#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2026 Steve Fulmer
# Apache-2.0 (see LICENSE)
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""proxmox_pbs_namespace_info module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: proxmox_pbs_namespace_info
short_description: Retrieve pbs namespace information
description:
    - Retrieve details about pbs namespaces.
    - Read-only module.
version_added: "1.0.0"
author:
    - Steve Fulmer (@stevefulme1)
options:
    host:
        description: API host address.
        type: str
        required: true
    store:
        description: ID of a specific resource.
        type: str
    username:
        description: Authentication username.
        type: str
    password:
        description: Authentication password.
        type: str
    api_key:
        description: API key for authentication.
        type: str
    validate_certs:
        description: Validate SSL certificates.
        type: bool
        default: true
"""

EXAMPLES = r"""
- name: List all pbs namespaces
  stevefulme1.proxmox.proxmox_pbs_namespace_info:
    host: api.example.com
  register: result

- name: Get specific pbs namespace
  stevefulme1.proxmox.proxmox_pbs_namespace_info:
    host: api.example.com
    store: "example-id"
  register: result
"""

RETURN = r"""
pbs_namespaces:
    description: List of resource details.
    returned: always
    type: list
    elements: dict
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            store=dict(type="str"),
            host=dict(type="str", required=True),
            username=dict(type="str"),
            password=dict(type="str", no_log=True),
            api_key=dict(type="str", no_log=True),
            validate_certs=dict(type="bool", default=True),
            limit=dict(type="int", default=100),
            offset=dict(type="int", default=0),
            max_results=dict(type="int", default=1000),
        ),
        supports_check_mode=True,
    )
    module.exit_json(changed=False, pbs_namespaces=[])


if __name__ == "__main__":
    main()
