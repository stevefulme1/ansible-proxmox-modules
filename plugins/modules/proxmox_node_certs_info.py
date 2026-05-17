#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_certs_info
short_description: Query certificate information on Proxmox VE nodes
version_added: "1.0.0"
description:
  - Retrieve certificate chain details from a Proxmox VE node via the
    C(/nodes/{node}/certificates/info) API endpoint.
  - This is an info module and does not make any changes.
options:
  api_host:
    description: Proxmox VE API host (hostname or IP).
    type: str
    required: true
  api_user:
    description: Proxmox VE API user (e.g. C(root@pam)).
    type: str
    required: true
  api_password:
    description: Password for API user.
    type: str
  api_token_id:
    description: API token ID.
    type: str
  api_token_secret:
    description: API token secret.
    type: str
  validate_certs:
    description: Whether to validate SSL certificates.
    type: bool
    default: true
  node:
    description: Target Proxmox VE node name.
    type: str
    required: true
author:
  - sfulmer
  limit:
    description:
      - Maximum number of results to return.
    type: int
    default: 100
  offset:
    description:
      - Number of results to skip for pagination.
    type: int
    default: 0
  max_results:
    description:
      - Maximum total results to return.
    type: int
    default: 1000
'''

EXAMPLES = r'''
- name: Get certificate information
  stevefulme1.proxmox.proxmox_node_certs_info:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
  register: cert_info

- name: Show certificate subjects
  ansible.builtin.debug:
    msg: "{{ item.subject }}"
  loop: "{{ cert_info.certificates }}"
'''

RETURN = r'''
certificates:
  description: List of certificate details in the node certificate chain.
  returned: success
  type: list
  elements: dict
  sample:
    - filename: "pveproxy-ssl.pem"
      subject: "/CN=pve1.example.com"
      issuer: "/CN=Proxmox Virtual Environment"
      notafter: 1735689600
      notbefore: 1704067200
      fingerprint: "AA:BB:CC:DD:..."
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    argument_spec = dict(
        limit=dict(type='int', default=100),
        offset=dict(type='int', default=0),
        max_results=dict(type='int', default=1000),
        node=dict(type='str', required=True),
    )

    proxmox = ProxmoxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module = proxmox.module
    node = module.params['node']

    api = proxmox.get_api()

    try:
        certs = api.nodes(node).certificates.info.get()
    except Exception as e:
        module.fail_json(
            msg="Failed to query certificate info on node '%s': %s" % (node, str(e)))

    module.exit_json(changed=False, certificates=certs)


if __name__ == '__main__':
    main()
