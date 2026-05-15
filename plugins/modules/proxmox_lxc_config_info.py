#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_lxc_config_info
short_description: Get LXC container configuration on Proxmox VE
version_added: "1.1.0"
description:
  - Retrieve the full configuration of a specific LXC container.
  - Returns all config keys such as hostname, memory, rootfs, net, and more.
  - This is an info module and does not make any changes.
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node where the container resides.
    type: str
    required: true
  vmid:
    description:
      - The container ID to query configuration for.
    type: int
    required: true
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Get container configuration
  stevefulme1.proxmox.proxmox_lxc_config_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 200
  register: ct_config

- name: Display container config
  ansible.builtin.debug:
    var: ct_config.resources
'''

RETURN = r'''
resources:
  description: Container configuration dictionary.
  returned: always
  type: dict
  sample:
    arch: "amd64"
    cores: 2
    hostname: "dns-server"
    memory: 512
    net0: "name=eth0,bridge=vmbr0,ip=dhcp"
    ostype: "ubuntu"
    rootfs: "local-lvm:vm-200-disk-0,size=8G"
    swap: 512
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            vmid=dict(type='int', required=True),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    vmid = module.params['vmid']

    proxmox = module.proxmox_api()

    try:
        config = proxmox.nodes(node).lxc(vmid).config.get()
    except Exception as e:
        module.fail_json(
            msg="Failed to get config for container {0} on node '{1}': {2}".format(
                vmid, node, str(e)
            )
        )

    module.exit_json(changed=False, resources=config)


if __name__ == '__main__':
    main()
