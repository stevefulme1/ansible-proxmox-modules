#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pool
short_description: Manage resource pools on Proxmox VE
version_added: "1.0.0"
description:
  - Create, update, or delete resource pools on Proxmox VE.
  - Supports managing pool membership (VMs, containers, and storage).
author:
  - sfulmer
options:
  poolid:
    description:
      - The unique identifier for the resource pool.
    type: str
    required: true
  comment:
    description:
      - A comment or description for the pool.
    type: str
  members:
    description:
      - List of members to assign to the pool.
      - Each member is a dict with C(vmid) and C(type) keys (for VMs/containers), or a C(storage) key.
      - Type should be C(qemu) for VMs or C(lxc) for containers.
    type: list
    elements: dict
  state:
    description:
      - C(present) ensures the pool exists with the specified configuration.
      - C(absent) removes the pool.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - sfulmer.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create a resource pool
  sfulmer.proxmox.proxmox_pool:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    poolid: production
    comment: Production workloads
    state: present

- name: Create pool with members
  sfulmer.proxmox.proxmox_pool:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    poolid: webservers
    comment: Web server pool
    members:
      - vmid: 100
        type: qemu
      - vmid: 101
        type: lxc
      - storage: local-lvm
    state: present

- name: Delete a resource pool
  sfulmer.proxmox.proxmox_pool:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    poolid: production
    state: absent
'''

RETURN = r'''
poolid:
  description: The pool identifier.
  returned: always
  type: str
  sample: production
pool:
  description: The pool configuration after changes.
  returned: success and state is present
  type: dict
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            poolid=dict(type='str', required=True),
            comment=dict(type='str'),
            members=dict(type='list', elements='dict'),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True,
    )

    poolid = module.params['poolid']
    comment = module.params['comment']
    members = module.params['members']
    state = module.params['state']

    proxmox = module.proxmox_api()

    # Check if pool exists
    pool_exists = False
    existing_pool = None
    try:
        pools = proxmox.pools.get()
        for pool in pools:
            if pool.get('poolid') == poolid:
                pool_exists = True
                break
        if pool_exists:
            existing_pool = proxmox.pools(poolid).get()
    except Exception as e:
        module.fail_json(msg="Failed to query pools: {0}".format(str(e)))

    if state == 'absent':
        if not pool_exists:
            module.exit_json(changed=False, poolid=poolid)

        if module.check_mode:
            module.exit_json(changed=True, poolid=poolid)

        try:
            proxmox.pools(poolid).delete()
        except Exception as e:
            module.fail_json(msg="Failed to delete pool '{0}': {1}".format(poolid, str(e)))

        module.exit_json(changed=True, poolid=poolid)

    # state == 'present'
    changed = False

    if not pool_exists:
        if module.check_mode:
            module.exit_json(changed=True, poolid=poolid)

        try:
            create_params = dict(poolid=poolid)
            if comment is not None:
                create_params['comment'] = comment
            proxmox.pools.post(**create_params)
            changed = True
        except Exception as e:
            module.fail_json(msg="Failed to create pool '{0}': {1}".format(poolid, str(e)))
    else:
        # Update comment if changed
        if comment is not None and existing_pool.get('comment', '') != comment:
            if module.check_mode:
                module.exit_json(changed=True, poolid=poolid)

            try:
                proxmox.pools(poolid).put(comment=comment)
                changed = True
            except Exception as e:
                module.fail_json(msg="Failed to update pool '{0}': {1}".format(poolid, str(e)))

    # Handle members
    if members is not None:
        existing_members = existing_pool.get('members', []) if existing_pool else []

        existing_vmids = set()
        existing_storages = set()
        for m in existing_members:
            if 'vmid' in m:
                existing_vmids.add(int(m['vmid']))
            if m.get('type') == 'storage' and 'storage' in m:
                existing_storages.add(m['storage'])

        vms_to_add = []
        storages_to_add = []

        for member in members:
            if 'vmid' in member:
                vmid_val = int(member['vmid'])
                if vmid_val not in existing_vmids:
                    vms_to_add.append(member)
            elif 'storage' in member:
                if member['storage'] not in existing_storages:
                    storages_to_add.append(member)

        if vms_to_add or storages_to_add:
            if module.check_mode:
                module.exit_json(changed=True, poolid=poolid)

            for member in vms_to_add:
                try:
                    proxmox.pools(poolid).put(
                        vms=str(member['vmid']),
                    )
                    changed = True
                except Exception as e:
                    module.fail_json(
                        msg="Failed to add VM {0} to pool '{1}': {2}".format(
                            member['vmid'], poolid, str(e)
                        )
                    )

            for member in storages_to_add:
                try:
                    proxmox.pools(poolid).put(
                        storage=member['storage'],
                    )
                    changed = True
                except Exception as e:
                    module.fail_json(
                        msg="Failed to add storage '{0}' to pool '{1}': {2}".format(
                            member['storage'], poolid, str(e)
                        )
                    )

    # Retrieve final pool state
    try:
        final_pool = proxmox.pools(poolid).get()
    except Exception:
        final_pool = {}

    module.exit_json(changed=changed, poolid=poolid, pool=final_pool)


if __name__ == '__main__':
    main()
