#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_storage
short_description: Manage storage definitions in Proxmox VE
description:
  - Create, update, or remove storage definitions in Proxmox VE.
  - Supports LVM, ZFS, NFS, CIFS, iSCSI, Ceph RBD, CephFS, Directory, GlusterFS, and PBS storage types.
  - Uses the C(/storage) API endpoint.
version_added: "1.0.0"
author:
  - sfulmer
options:
  storage:
    description:
      - The storage identifier name.
    type: str
    required: true
  type:
    description:
      - The storage type.
    type: str
    choices: ['lvm', 'zfspool', 'nfs', 'cifs', 'iscsi', 'rbd', 'cephfs', 'dir', 'glusterfs', 'pbs']
  path:
    description:
      - File system path for directory-based storage.
    type: str
  server:
    description:
      - Server address for network storage (NFS, CIFS, iSCSI, Ceph, GlusterFS, PBS).
    type: str
  export:
    description:
      - NFS export path.
    type: str
  volume:
    description:
      - GlusterFS volume name or iSCSI target.
    type: str
  pool:
    description:
      - Ceph RBD pool name or ZFS pool name.
    type: str
  content:
    description:
      - List of content types to store.
    type: list
    elements: str
  nodes:
    description:
      - List of cluster nodes where this storage is available.
    type: list
    elements: str
  shared:
    description:
      - Whether the storage is shared across nodes.
    type: bool
  disable:
    description:
      - Whether the storage is disabled.
    type: bool
  state:
    description:
      - Whether the storage should be present or absent.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create an NFS storage
  stevefulme1.proxmox.proxmox_storage:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    storage: nfs-backup
    type: nfs
    server: 192.168.1.100
    export: /mnt/backup
    content:
      - backup
      - iso
    state: present

- name: Create a directory storage
  stevefulme1.proxmox.proxmox_storage:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    storage: local-images
    type: dir
    path: /mnt/images
    content:
      - images
      - iso
    state: present

- name: Remove a storage definition
  stevefulme1.proxmox.proxmox_storage:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    storage: nfs-backup
    state: absent
'''

RETURN = r'''
storage:
  description: The storage identifier that was managed.
  returned: success
  type: str
  sample: "nfs-backup"
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def get_storage(api, storage_id):
    """Return storage config dict or None if not found."""
    try:
        return api.storage(storage_id).get()
    except Exception:
        return None


def main():
    module_args = dict(
        storage=dict(type='str', required=True),
        type=dict(type='str', choices=['lvm', 'zfspool', 'nfs', 'cifs', 'iscsi', 'rbd', 'cephfs', 'dir', 'glusterfs', 'pbs']),
        path=dict(type='str'),
        server=dict(type='str'),
        export=dict(type='str'),
        volume=dict(type='str'),
        pool=dict(type='str'),
        content=dict(type='list', elements='str'),
        nodes=dict(type='list', elements='str'),
        shared=dict(type='bool'),
        disable=dict(type='bool'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    proxmox = ProxmoxModule(
        argument_spec=module_args,
        required_if=[
            ('state', 'present', ['type']),
        ],
    )
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    storage_id = params['storage']
    state = params['state']
    existing = get_storage(api, storage_id)
    changed = False
    result = dict(storage=storage_id)

    if state == 'absent':
        if existing is not None:
            changed = True
            if not module.check_mode:
                try:
                    api.storage(storage_id).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete storage '%s': %s" % (storage_id, str(e)))
        module.exit_json(changed=changed, **result)

    # state == present
    # Build the desired parameters
    config_keys = ['path', 'server', 'export', 'volume', 'pool', 'shared', 'disable']
    desired = {}
    for key in config_keys:
        if params.get(key) is not None:
            desired[key] = params[key]

    if params.get('content') is not None:
        desired['content'] = ','.join(params['content'])
    if params.get('nodes') is not None:
        desired['nodes'] = ','.join(params['nodes'])

    if existing is None:
        # Create
        changed = True
        if not module.check_mode:
            create_params = dict(storage=storage_id, type=params['type'])
            create_params.update(desired)
            try:
                api.storage.post(**create_params)
            except Exception as e:
                module.fail_json(msg="Failed to create storage '%s': %s" % (storage_id, str(e)))
    else:
        # Update - check for differences
        update_params = {}
        for key, value in desired.items():
            current_val = existing.get(key)
            if isinstance(value, bool):
                current_bool = bool(current_val) if current_val is not None else False
                if current_bool != value:
                    update_params[key] = int(value)
            elif str(current_val or '') != str(value):
                update_params[key] = value

        if update_params:
            changed = True
            if not module.check_mode:
                try:
                    api.storage(storage_id).put(**update_params)
                except Exception as e:
                    module.fail_json(msg="Failed to update storage '%s': %s" % (storage_id, str(e)))

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
