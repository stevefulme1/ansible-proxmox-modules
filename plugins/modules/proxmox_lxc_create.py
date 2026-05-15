#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_lxc_create
short_description: Create an LXC container in Proxmox VE
description:
  - Create a new LXC container from scratch in Proxmox VE.
  - Requires an OS template to be available on the target node.
  - If I(vmid) is not provided, Proxmox will auto-assign the next available ID.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node on which to create the container.
    type: str
    required: true
  vmid:
    description:
      - The container ID to assign. If not specified, the next available ID is used.
    type: int
  hostname:
    description:
      - The hostname of the container.
    type: str
  ostemplate:
    description:
      - The OS template to use (e.g. C(local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst)).
    type: str
    required: true
  memory:
    description:
      - Amount of RAM in MiB.
    type: int
    default: 512
  swap:
    description:
      - Amount of swap in MiB.
    type: int
    default: 512
  cores:
    description:
      - Number of CPU cores.
    type: int
    default: 1
  rootfs:
    description:
      - Root filesystem specification (e.g. C(local-lvm:8) for 8 GiB on local-lvm).
    type: str
  net0:
    description:
      - Network device specification (e.g. C(name=eth0,bridge=vmbr0,ip=dhcp)).
    type: str
  password:
    description:
      - Root password for the container.
    type: str
    no_log: true
  ssh_public_keys:
    description:
      - SSH public keys to add to the container, one per line.
    type: str
  start_after_create:
    description:
      - Whether to start the container immediately after creation.
    type: bool
    default: false
  unprivileged:
    description:
      - Whether to create an unprivileged container.
    type: bool
    default: true
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create a basic LXC container
  stevefulme1.proxmox.proxmox_lxc_create:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    hostname: my-container
    ostemplate: "local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst"
    memory: 1024
    cores: 2
    rootfs: "local-lvm:8"
    net0: "name=eth0,bridge=vmbr0,ip=dhcp"
    start_after_create: true

- name: Create an unprivileged container with SSH key
  stevefulme1.proxmox.proxmox_lxc_create:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    hostname: web-server
    ostemplate: "local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst"
    memory: 2048
    swap: 1024
    cores: 4
    rootfs: "local-lvm:16"
    net0: "name=eth0,bridge=vmbr0,ip=10.0.0.50/24,gw=10.0.0.1"
    ssh_public_keys: "ssh-ed25519 AAAA... user@host"
    unprivileged: true
'''

RETURN = r'''
vmid:
  description: The container ID of the created LXC container.
  type: int
  returned: always
  sample: 101
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "LXC container 101 created successfully on node pve1."
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


def main():
    module_args = dict(
        node=dict(type='str', required=True),
        vmid=dict(type='int'),
        hostname=dict(type='str'),
        ostemplate=dict(type='str', required=True),
        memory=dict(type='int', default=512),
        swap=dict(type='int', default=512),
        cores=dict(type='int', default=1),
        rootfs=dict(type='str'),
        net0=dict(type='str'),
        password=dict(type='str', no_log=True),
        ssh_public_keys=dict(type='str', no_log=False),
        start_after_create=dict(type='bool', default=False),
        unprivileged=dict(type='bool', default=True),
    )

    proxmox = ProxmoxModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    node = params['node']

    # Build the creation parameters
    create_params = dict(
        ostemplate=params['ostemplate'],
    )

    if params['vmid']:
        create_params['vmid'] = params['vmid']
    else:
        try:
            create_params['vmid'] = api.cluster.nextid.get()
        except Exception as e:
            module.fail_json(msg="Failed to get next available VMID: %s" % str(e))

    vmid = int(create_params['vmid'])

    # Check if container already exists
    try:
        existing_cts = api.nodes(node).lxc.get()
        for ct in existing_cts:
            if int(ct.get('vmid', 0)) == vmid:
                module.exit_json(changed=False, vmid=vmid, msg="LXC container %d already exists on node %s." % (vmid, node))
    except Exception as e:
        module.fail_json(msg="Failed to check existing containers: %s" % str(e))

    # Map module params to API params
    param_map = {
        'hostname': 'hostname',
        'memory': 'memory',
        'swap': 'swap',
        'cores': 'cores',
        'rootfs': 'rootfs',
        'net0': 'net0',
        'password': 'password',
    }

    for module_param, api_param in param_map.items():
        if params.get(module_param) is not None:
            create_params[api_param] = params[module_param]

    if params.get('ssh_public_keys'):
        create_params['ssh-public-keys'] = params['ssh_public_keys']

    if params['unprivileged']:
        create_params['unprivileged'] = 1
    else:
        create_params['unprivileged'] = 0

    if module.check_mode:
        module.exit_json(changed=True, vmid=vmid, msg="LXC container %d would be created on node %s." % (vmid, node))

    try:
        api.nodes(node).lxc.create(**create_params)
    except Exception as e:
        module.fail_json(msg="Failed to create LXC container %d on node %s: %s" % (vmid, node, str(e)))

    # Optionally start the container after creation
    if params['start_after_create']:
        try:
            api.nodes(node).lxc(vmid).status.start.post()
        except Exception as e:
            module.fail_json(msg="LXC container %d created but failed to start: %s" % (vmid, str(e)))

    module.exit_json(changed=True, vmid=vmid, msg="LXC container %d created successfully on node %s." % (vmid, node))


if __name__ == '__main__':
    main()
