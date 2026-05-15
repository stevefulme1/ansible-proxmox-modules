#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_firewall_rule_info
short_description: List firewall rules on Proxmox VE
version_added: "1.1.0"
description:
  - Retrieve firewall rules at the cluster, node, or VM level.
  - This is an info module and does not make any changes.
author:
  - sfulmer
options:
  scope:
    description:
      - The scope at which to query firewall rules.
      - C(cluster) queries C(/cluster/firewall/rules).
      - C(node) queries C(/nodes/{node}/firewall/rules).
      - C(vm) queries C(/nodes/{node}/qemu/{vmid}/firewall/rules).
    type: str
    required: true
    choices: ['cluster', 'node', 'vm']
  node:
    description:
      - The Proxmox VE node name.
      - Required when I(scope) is C(node) or C(vm).
    type: str
  vmid:
    description:
      - The VM ID to query firewall rules for.
      - Required when I(scope) is C(vm).
    type: int
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: List cluster firewall rules
  stevefulme1.proxmox.proxmox_firewall_rule_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    scope: cluster
  register: cluster_rules

- name: List node firewall rules
  stevefulme1.proxmox.proxmox_firewall_rule_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    scope: node
    node: pve1
  register: node_rules

- name: List VM firewall rules
  stevefulme1.proxmox.proxmox_firewall_rule_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    scope: vm
    node: pve1
    vmid: 100
  register: vm_rules

- name: Display rules
  ansible.builtin.debug:
    var: cluster_rules.resources
'''

RETURN = r'''
resources:
  description: List of firewall rules.
  returned: always
  type: list
  elements: dict
  sample:
    - pos: 0
      type: "in"
      action: "ACCEPT"
      proto: "tcp"
      dport: "22"
      enable: 1
      comment: "Allow SSH"
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            scope=dict(
                type='str', required=True,
                choices=['cluster', 'node', 'vm'],
            ),
            node=dict(type='str'),
            vmid=dict(type='int'),
        ),
        required_if=[
            ('scope', 'node', ['node']),
            ('scope', 'vm', ['node', 'vmid']),
        ],
        supports_check_mode=True,
    )

    scope = module.params['scope']
    node = module.params['node']
    vmid = module.params['vmid']

    proxmox = module.proxmox_api()

    try:
        if scope == 'cluster':
            rules = proxmox.cluster.firewall.rules.get()
        elif scope == 'node':
            rules = proxmox.nodes(node).firewall.rules.get()
        else:
            rules = proxmox.nodes(node).qemu(vmid).firewall.rules.get()
    except Exception as e:
        module.fail_json(
            msg="Failed to list {0} firewall rules: {1}".format(
                scope, str(e)
            )
        )

    module.exit_json(changed=False, resources=rules)


if __name__ == '__main__':
    main()
