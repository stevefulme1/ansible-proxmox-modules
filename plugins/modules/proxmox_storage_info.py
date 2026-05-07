#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_storage_info
short_description: List and query storage configurations in Proxmox VE
description:
  - Retrieve storage configuration information from a Proxmox VE cluster.
  - This is an info module that does not modify state.
  - Uses the C(/storage) API endpoint.
version_added: "1.0.0"
author:
  - sfulmer
options:
  type:
    description:
      - Filter results by storage type.
      - If not specified, all storage configurations are returned.
    type: str
    choices: ['lvm', 'zfspool', 'nfs', 'cifs', 'iscsi', 'rbd', 'cephfs', 'dir', 'glusterfs', 'pbs']
'''

EXAMPLES = r'''
- name: List all storage configurations
  stevefulme1.proxmox.proxmox_storage_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
  register: all_storage

- name: List only NFS storage
  stevefulme1.proxmox.proxmox_storage_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    type: nfs
  register: nfs_storage

- name: Display storage list
  ansible.builtin.debug:
    var: all_storage.storages
'''

RETURN = r'''
storages:
  description: List of storage configurations.
  returned: always
  type: list
  elements: dict
  sample:
    - storage: "local"
      type: "dir"
      path: "/var/lib/vz"
      content: "images,iso,vztmpl"
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        type=dict(type='str', choices=['lvm', 'zfspool', 'nfs', 'cifs', 'iscsi', 'rbd', 'cephfs', 'dir', 'glusterfs', 'pbs']),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    try:
        query_params = {}
        if params.get('type'):
            query_params['type'] = params['type']
        storages = api.storage.get(**query_params)
    except Exception as e:
        module.fail_json(msg="Failed to get storage configurations: %s" % str(e))

    module.exit_json(changed=False, storages=storages)


if __name__ == '__main__':
    main()
