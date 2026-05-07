#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_lvm
short_description: Manage LVM volume groups on Proxmox VE nodes
version_added: "1.0.0"
description:
  - Create LVM or LVM-thin volume groups on Proxmox VE nodes via the
    C(/nodes/{node}/disks/lvm) and C(/nodes/{node}/disks/lvmthin) API endpoints.
  - LVM volume groups cannot be easily removed via the Proxmox API, so only
    C(state=present) is supported.
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
    description: The LVM volume group name.
    type: str
    required: true
  device:
    description:
      - The block device to use for the volume group (e.g. C(/dev/sdb)).
      - Required when creating a new volume group.
    type: str
  add_storage:
    description:
      - Whether to automatically add the volume group as a Proxmox storage.
    type: bool
    default: true
  thin:
    description:
      - If C(true), create an LVM-thin pool instead of a standard LVM VG.
    type: bool
    default: false
  state:
    description:
      - Only C(present) is supported. LVM VGs cannot be removed via the API.
    type: str
    choices: ['present']
    default: present
author:
  - sfulmer
'''

EXAMPLES = r'''
- name: Create an LVM volume group
  stevefulme1.proxmox.proxmox_node_lvm:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    name: vg_data
    device: /dev/sdb

- name: Create an LVM-thin pool
  stevefulme1.proxmox.proxmox_node_lvm:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    name: thinpool_data
    device: /dev/sdc
    thin: true
    add_storage: true
'''

RETURN = r'''
name:
  description: The LVM volume group name.
  returned: success
  type: str
  sample: "vg_data"
upid:
  description: The task UPID returned by the API for creation.
  returned: when created, not check_mode
  type: str
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def vg_exists(api, node, name, thin):
    """Check if a volume group already exists."""
    try:
        if thin:
            vgs = api.nodes(node).disks.lvmthin.get()
        else:
            vgs = api.nodes(node).disks.lvm.get()
        for vg in vgs:
            if vg.get('vg', vg.get('lv', '')) == name or vg.get('name', '') == name:
                return True
    except Exception:
        pass
    return False


def main():
    argument_spec = dict(
        node=dict(type='str', required=True),
        name=dict(type='str', required=True),
        device=dict(type='str'),
        add_storage=dict(type='bool', default=True),
        thin=dict(type='bool', default=False),
        state=dict(type='str', default='present', choices=['present']),
    )

    proxmox = ProxmoxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module = proxmox.module
    params = module.params
    node = params['node']
    name = params['name']
    thin = params['thin']

    api = proxmox.get_api()
    result = dict(name=name)

    if vg_exists(api, node, name, thin):
        module.exit_json(changed=False, **result)

    # Need to create - device is required
    if not params.get('device'):
        module.fail_json(
            msg="Parameter 'device' is required when creating a new LVM volume group.")

    changed = True
    if not module.check_mode:
        post_params = dict(
            name=name,
            device=params['device'],
            add_storage=1 if params['add_storage'] else 0,
        )
        try:
            if thin:
                upid = api.nodes(node).disks.lvmthin.post(**post_params)
            else:
                upid = api.nodes(node).disks.lvm.post(**post_params)
            result['upid'] = upid
        except Exception as e:
            module.fail_json(
                msg="Failed to create %s volume group '%s' on node '%s': %s"
                % ('LVM-thin' if thin else 'LVM', name, node, str(e)))

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
