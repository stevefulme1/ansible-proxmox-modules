#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_certificate_info
short_description: List node certificates on Proxmox VE
version_added: "1.1.0"
description:
  - Retrieve certificate information for a Proxmox VE node.
  - Returns fingerprint, issuer, subject, notafter, and notbefore for each certificate.
  - This is an info module and does not make any changes.
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node to query certificates from.
    type: str
    required: true
  limit:
    description:
      - Maximum number of results to return.
      - Applied client-side to truncate results.
    type: int
    default: 100
  offset:
    description:
      - Number of results to skip before returning.
      - Applied client-side for pagination.
    type: int
    default: 0
  max_results:
    description:
      - Maximum total number of results to return.
      - Set to 0 for no limit.
    type: int
    default: 1000
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: List node certificates
  stevefulme1.proxmox.proxmox_certificate_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
  register: certs

- name: Display certificates
  ansible.builtin.debug:
    var: certs.resources
'''

RETURN = r'''
resources:
  description: List of certificates on the node.
  returned: always
  type: list
  elements: dict
  sample:
    - fingerprint: "AB:CD:EF:12:34:56:78:90"
      issuer: "CN=Proxmox Virtual Environment"
      subject: "/CN=pve1.example.com"
      notafter: 1735689600
      notbefore: 1704067200
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            limit=dict(type='int', default=100),
            offset=dict(type='int', default=0),
            max_results=dict(type='int', default=1000),
            node=dict(type='str', required=True),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']

    proxmox = module.proxmox_api()

    try:
        certs = proxmox.nodes(node).certificates.info.get()
    except Exception as e:
        module.fail_json(
            msg="Failed to list certificates on node '{0}': {1}".format(
                node, str(e)
            )
        )

    module.exit_json(changed=False, resources=certs)


if __name__ == '__main__':
    main()
