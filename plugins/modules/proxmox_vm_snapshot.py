#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_snapshot
short_description: Manage VM snapshots in Proxmox VE
description:
  - Create, delete, or rollback QEMU/KVM virtual machine snapshots in Proxmox VE.
  - Uses the C(/nodes/{node}/qemu/{vmid}/snapshot) API endpoint.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node name where the VM resides.
    type: str
    required: true
  vmid:
    description:
      - The VM ID number.
    type: int
    required: true
  snapname:
    description:
      - The snapshot name.
    type: str
    required: true
  description:
    description:
      - Description for the snapshot.
    type: str
  vmstate:
    description:
      - Whether to include RAM state in the snapshot.
    type: bool
    default: false
  state:
    description:
      - C(present) creates the snapshot if it does not exist.
      - C(absent) deletes the snapshot.
      - C(rollback) rolls back the VM to the snapshot.
    type: str
    choices: ['present', 'absent', 'rollback']
    default: present
'''

EXAMPLES = r'''
- name: Create a snapshot
  stevefulme1.proxmox.proxmox_vm_snapshot:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    snapname: pre-upgrade
    description: "Snapshot before OS upgrade"
    vmstate: true
    state: present

- name: Rollback to a snapshot
  stevefulme1.proxmox.proxmox_vm_snapshot:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    snapname: pre-upgrade
    state: rollback

- name: Delete a snapshot
  stevefulme1.proxmox.proxmox_vm_snapshot:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    snapname: pre-upgrade
    state: absent
'''

RETURN = r'''
vmid:
  description: The VM ID.
  returned: success
  type: int
  sample: 100
snapname:
  description: The snapshot name.
  returned: success
  type: str
  sample: "pre-upgrade"
upid:
  description: The task UPID for asynchronous operations.
  returned: when a task is started
  type: str
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def get_snapshot(api, node, vmid, snapname):
    """Check if a snapshot exists. Return snapshot dict or None."""
    try:
        snapshots = api.nodes(node).qemu(vmid).snapshot.get()
        for snap in snapshots:
            if snap.get('name') == snapname:
                return snap
        return None
    except Exception:
        return None


def main():
    module_args = dict(
        node=dict(type='str', required=True),
        vmid=dict(type='int', required=True),
        snapname=dict(type='str', required=True),
        description=dict(type='str'),
        vmstate=dict(type='bool', default=False),
        state=dict(type='str', default='present', choices=['present', 'absent', 'rollback']),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    node = params['node']
    vmid = params['vmid']
    snapname = params['snapname']
    state = params['state']
    changed = False
    result = dict(vmid=vmid, snapname=snapname)

    existing = get_snapshot(api, node, vmid, snapname)

    if state == 'absent':
        if existing is not None:
            changed = True
            if not module.check_mode:
                try:
                    upid = api.nodes(node).qemu(vmid).snapshot(snapname).delete()
                    result['upid'] = upid
                except Exception as e:
                    module.fail_json(msg="Failed to delete snapshot '%s' on VM %d: %s" % (snapname, vmid, str(e)))
        module.exit_json(changed=changed, **result)

    if state == 'rollback':
        if existing is None:
            module.fail_json(msg="Snapshot '%s' does not exist on VM %d, cannot rollback." % (snapname, vmid))
        changed = True
        if not module.check_mode:
            try:
                upid = api.nodes(node).qemu(vmid).snapshot(snapname).rollback.post()
                result['upid'] = upid
            except Exception as e:
                module.fail_json(msg="Failed to rollback to snapshot '%s' on VM %d: %s" % (snapname, vmid, str(e)))
        module.exit_json(changed=changed, **result)

    # state == present
    if existing is not None:
        module.exit_json(changed=False, **result)

    changed = True
    if not module.check_mode:
        snap_params = dict(snapname=snapname)
        if params.get('description'):
            snap_params['description'] = params['description']
        if params['vmstate']:
            snap_params['vmstate'] = 1
        try:
            upid = api.nodes(node).qemu(vmid).snapshot.post(**snap_params)
            result['upid'] = upid
        except Exception as e:
            module.fail_json(msg="Failed to create snapshot '%s' on VM %d: %s" % (snapname, vmid, str(e)))

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
