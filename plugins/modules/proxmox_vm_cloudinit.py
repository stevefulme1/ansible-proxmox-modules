#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_cloudinit
short_description: Manage cloud-init configuration for VMs in Proxmox VE
description:
  - Configure cloud-init parameters for a virtual machine in Proxmox VE.
  - Compares current cloud-init settings and only applies changes when needed.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox node the VM resides on.
    type: str
    required: true
  vmid:
    description:
      - The VM ID.
    type: int
    required: true
  ciuser:
    description:
      - Cloud-init user name.
    type: str
  cipassword:
    description:
      - Cloud-init user password.
    type: str
    no_log: true
  sshkeys:
    description:
      - URL-encoded SSH public keys for cloud-init.
    type: str
  ipconfig0:
    description:
      - IP configuration for the first network interface.
      - Example C(ip=10.0.0.1/24,gw=10.0.0.254) or C(ip=dhcp).
    type: str
  ipconfig1:
    description:
      - IP configuration for the second network interface.
    type: str
  ipconfig2:
    description:
      - IP configuration for the third network interface.
    type: str
  ipconfig3:
    description:
      - IP configuration for the fourth network interface.
    type: str
  ipconfig4:
    description:
      - IP configuration for the fifth network interface.
    type: str
  ipconfig5:
    description:
      - IP configuration for the sixth network interface.
    type: str
  ipconfig6:
    description:
      - IP configuration for the seventh network interface.
    type: str
  ipconfig7:
    description:
      - IP configuration for the eighth network interface.
    type: str
  ipconfig8:
    description:
      - IP configuration for the ninth network interface.
    type: str
  ipconfig9:
    description:
      - IP configuration for the tenth network interface.
    type: str
  ipconfig10:
    description:
      - IP configuration for the eleventh network interface.
    type: str
  ipconfig11:
    description:
      - IP configuration for the twelfth network interface.
    type: str
  ipconfig12:
    description:
      - IP configuration for the thirteenth network interface.
    type: str
  ipconfig13:
    description:
      - IP configuration for the fourteenth network interface.
    type: str
  ipconfig14:
    description:
      - IP configuration for the fifteenth network interface.
    type: str
  ipconfig15:
    description:
      - IP configuration for the sixteenth network interface.
    type: str
  nameserver:
    description:
      - DNS server address(es) for cloud-init.
    type: str
  searchdomain:
    description:
      - DNS search domain for cloud-init.
    type: str
  citype:
    description:
      - Cloud-init configuration format type.
    type: str
    choices:
      - configdrive2
      - nocloud
      - opennebula
  cicustom:
    description:
      - Custom cloud-init configuration snippet reference.
    type: str
  state:
    description:
      - Only C(present) is supported for cloud-init configuration.
    type: str
    default: present
    choices:
      - present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Configure cloud-init with static IP
  stevefulme1.proxmox.proxmox_vm_cloudinit:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    ciuser: admin
    cipassword: secret
    ipconfig0: "ip=10.0.0.10/24,gw=10.0.0.1"
    nameserver: "8.8.8.8 8.8.4.4"
    searchdomain: example.com
    state: present

- name: Configure cloud-init with DHCP and SSH keys
  stevefulme1.proxmox.proxmox_vm_cloudinit:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    ciuser: deploy
    ipconfig0: "ip=dhcp"
    sshkeys: "ssh-rsa%20AAAAB3...%20user%40host"
    state: present
'''

RETURN = r'''
vmid:
  description: The VM ID whose cloud-init config was managed.
  type: int
  returned: always
  sample: 100
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "Cloud-init configuration updated for VM 100."
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


CI_PARAMS = [
    'ciuser', 'cipassword', 'sshkeys', 'nameserver', 'searchdomain',
    'citype', 'cicustom',
] + ['ipconfig{0}'.format(i) for i in range(16)]


def _build_desired(module):
    """Build desired cloud-init params from module params."""
    desired = {}
    for key in CI_PARAMS:
        value = module.params.get(key)
        if value is not None:
            desired[key] = value
    return desired


def _needs_update(current, desired):
    """Return True if any desired value differs from current config."""
    for key, value in desired.items():
        # cipassword is never returned by the API, always update if set
        if key == 'cipassword':
            return True
        current_value = current.get(key)
        if current_value is None and value is not None:
            return True
        if str(current_value) != str(value):
            return True
    return False


def main():
    arg_spec = dict(
        node=dict(type='str', required=True),
        vmid=dict(type='int', required=True),
        ciuser=dict(type='str'),
        cipassword=dict(type='str', no_log=True),
        sshkeys=dict(type='str'),
        nameserver=dict(type='str'),
        searchdomain=dict(type='str'),
        citype=dict(
            type='str',
            choices=['configdrive2', 'nocloud', 'opennebula'],
        ),
        cicustom=dict(type='str'),
        state=dict(type='str', default='present', choices=['present']),
    )
    # Add ipconfig0 through ipconfig15
    for i in range(16):
        arg_spec['ipconfig{0}'.format(i)] = dict(type='str')

    module = ProxmoxModule(
        argument_spec=arg_spec,
        supports_check_mode=True,
    )

    node = module.params['node']
    vmid = module.params['vmid']

    config_path = 'nodes/{0}/qemu/{1}/config'.format(node, vmid)
    current = module.proxmox_request('GET', config_path)
    desired = _build_desired(module)

    if not desired:
        module.exit_json(
            changed=False, vmid=vmid,
            msg="No cloud-init parameters specified.",
        )

    changed = _needs_update(current, desired)

    if changed and not module.check_mode:
        module.proxmox_request('PUT', config_path, data=desired)

    msg = (
        "Cloud-init configuration updated for VM {0}.".format(vmid)
        if changed
        else "Cloud-init configuration already up to date for VM {0}.".format(
            vmid,
        )
    )

    module.exit_json(changed=changed, vmid=vmid, msg=msg)


if __name__ == '__main__':
    main()
