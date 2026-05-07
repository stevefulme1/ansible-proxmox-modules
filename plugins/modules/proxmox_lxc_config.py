#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_lxc_config
short_description: Modify LXC container configuration on Proxmox VE
version_added: "1.0.0"
description:
  - Modify configuration options for an existing LXC container on Proxmox VE.
  - Uses the Proxmox VE API to read current configuration and apply changes idempotently.
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node on which the container resides.
    type: str
    required: true
  vmid:
    description:
      - The unique ID of the container.
    type: int
    required: true
  hostname:
    description:
      - Set the hostname of the container.
    type: str
  memory:
    description:
      - Amount of RAM in MB for the container.
    type: int
  swap:
    description:
      - Amount of swap in MB for the container.
    type: int
  cores:
    description:
      - Number of CPU cores for the container.
    type: int
  cpulimit:
    description:
      - CPU limit (fraction of a single CPU core).
    type: float
  cpuunits:
    description:
      - CPU weight for the container.
    type: int
  description:
    description:
      - Description for the container.
    type: str
  nameserver:
    description:
      - DNS nameserver IP address(es).
    type: str
  searchdomain:
    description:
      - DNS search domain(s).
    type: str
  onboot:
    description:
      - Whether the container starts on boot.
    type: bool
  protection:
    description:
      - Whether the container is protected from removal.
    type: bool
  unprivileged:
    description:
      - Whether the container runs as unprivileged.
    type: bool
  state:
    description:
      - The desired state. Only C(present) is supported; it ensures the configuration matches.
    type: str
    choices: ['present']
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Set container hostname and memory
  stevefulme1.proxmox.proxmox_lxc_config:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    hostname: webserver
    memory: 2048

- name: Enable onboot and set cores
  stevefulme1.proxmox.proxmox_lxc_config:
    api_host: proxmox.example.com
    api_token_id: root@pam!mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    onboot: true
    cores: 4
'''

RETURN = r'''
vmid:
  description: The container ID that was configured.
  returned: always
  type: int
  sample: 100
config:
  description: The resulting container configuration after changes.
  returned: success
  type: dict
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            vmid=dict(type='int', required=True),
            hostname=dict(type='str'),
            memory=dict(type='int'),
            swap=dict(type='int'),
            cores=dict(type='int'),
            cpulimit=dict(type='float'),
            cpuunits=dict(type='int'),
            description=dict(type='str'),
            nameserver=dict(type='str'),
            searchdomain=dict(type='str'),
            onboot=dict(type='bool'),
            protection=dict(type='bool'),
            unprivileged=dict(type='bool'),
            state=dict(type='str', choices=['present'], default='present'),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    vmid = module.params['vmid']

    config_params = [
        'hostname', 'memory', 'swap', 'cores', 'cpulimit', 'cpuunits',
        'description', 'nameserver', 'searchdomain', 'onboot', 'protection',
        'unprivileged',
    ]

    proxmox = module.proxmox_api()

    try:
        current_config = proxmox.nodes(node).lxc(vmid).config.get()
    except Exception as e:
        module.fail_json(msg="Failed to get container {0} config: {1}".format(vmid, str(e)))

    changes = {}
    for param in config_params:
        value = module.params[param]
        if value is None:
            continue
        current_value = current_config.get(param)
        if isinstance(value, bool):
            api_value = 1 if value else 0
            if current_value != api_value:
                changes[param] = api_value
        else:
            if str(current_value) != str(value):
                changes[param] = value

    if not changes:
        module.exit_json(changed=False, vmid=vmid, config=current_config)

    if module.check_mode:
        module.exit_json(changed=True, vmid=vmid, config=current_config, changes=changes)

    try:
        proxmox.nodes(node).lxc(vmid).config.put(**changes)
        updated_config = proxmox.nodes(node).lxc(vmid).config.get()
    except Exception as e:
        module.fail_json(msg="Failed to update container {0} config: {1}".format(vmid, str(e)))

    module.exit_json(changed=True, vmid=vmid, config=updated_config)


if __name__ == '__main__':
    main()
