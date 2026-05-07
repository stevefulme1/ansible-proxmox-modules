#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_zfs
short_description: Manage ZFS pools on Proxmox VE nodes
version_added: "1.0.0"
description:
  - Create or destroy ZFS pools on Proxmox VE nodes via the
    C(/nodes/{node}/disks/zfs) API endpoint.
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
  name:
    description: The ZFS pool name.
    type: str
    required: true
  devices:
    description:
      - List of block devices to use for the ZFS pool.
      - Required when creating a new pool (C(state=present)).
    type: list
    elements: str
  raidlevel:
    description:
      - The RAID level for the ZFS pool.
      - Required when creating a new pool (C(state=present)).
    type: str
    choices: ['single', 'mirror', 'raid10', 'raidz', 'raidz2', 'raidz3']
  ashift:
    description:
      - Pool sector size exponent (ashift value, e.g. 12 for 4K sectors).
    type: int
  compression:
    description:
      - Compression algorithm for the ZFS pool.
    type: str
    choices: ['on', 'off', 'gzip', 'lz4', 'lzjb', 'zle', 'zstd']
  add_storage:
    description:
      - Whether to automatically add the pool as a Proxmox storage.
    type: bool
    default: true
  state:
    description:
      - Whether the ZFS pool should be present or absent.
    type: str
    choices: ['present', 'absent']
    default: present
author:
  - sfulmer
'''

EXAMPLES = r'''
- name: Create a ZFS mirror pool
  stevefulme1.proxmox.proxmox_node_zfs:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    name: tank
    devices:
      - /dev/sdb
      - /dev/sdc
    raidlevel: mirror
    compression: lz4

- name: Create a single-disk ZFS pool
  stevefulme1.proxmox.proxmox_node_zfs:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    name: fast_pool
    devices:
      - /dev/nvme0n1
    raidlevel: single
    ashift: 12

- name: Destroy a ZFS pool
  stevefulme1.proxmox.proxmox_node_zfs:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    name: tank
    state: absent
'''

RETURN = r'''
name:
  description: The ZFS pool name.
  returned: success
  type: str
  sample: "tank"
upid:
  description: The task UPID returned by the API.
  returned: when created or destroyed, not check_mode
  type: str
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def pool_exists(api, node, name):
    """Check if a ZFS pool already exists."""
    try:
        pools = api.nodes(node).disks.zfs.get()
        for pool in pools:
            if pool.get('name', '') == name:
                return True
    except Exception:
        pass
    return False


def main():
    argument_spec = dict(
        node=dict(type='str', required=True),
        name=dict(type='str', required=True),
        devices=dict(type='list', elements='str'),
        raidlevel=dict(type='str',
                       choices=['single', 'mirror', 'raid10', 'raidz', 'raidz2', 'raidz3']),
        ashift=dict(type='int'),
        compression=dict(type='str',
                         choices=['on', 'off', 'gzip', 'lz4', 'lzjb', 'zle', 'zstd']),
        add_storage=dict(type='bool', default=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    proxmox = ProxmoxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['devices', 'raidlevel']],
        ],
    )
    module = proxmox.module
    params = module.params
    node = params['node']
    name = params['name']
    state = params['state']

    api = proxmox.get_api()
    result = dict(name=name)
    exists = pool_exists(api, node, name)

    if state == 'absent':
        if not exists:
            module.exit_json(changed=False, **result)
        changed = True
        if not module.check_mode:
            try:
                upid = api.nodes(node).disks.zfs(name).delete()
                result['upid'] = upid
            except Exception as e:
                module.fail_json(
                    msg="Failed to destroy ZFS pool '%s' on node '%s': %s"
                    % (name, node, str(e)))
        module.exit_json(changed=changed, **result)

    # state == present
    if exists:
        module.exit_json(changed=False, **result)

    changed = True
    if not module.check_mode:
        post_params = dict(
            name=name,
            raidlevel=params['raidlevel'],
            devices=' '.join(params['devices']),
            add_storage=1 if params['add_storage'] else 0,
        )
        if params.get('ashift') is not None:
            post_params['ashift'] = params['ashift']
        if params.get('compression'):
            post_params['compression'] = params['compression']
        try:
            upid = api.nodes(node).disks.zfs.post(**post_params)
            result['upid'] = upid
        except Exception as e:
            module.fail_json(
                msg="Failed to create ZFS pool '%s' on node '%s': %s"
                % (name, node, str(e)))

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
