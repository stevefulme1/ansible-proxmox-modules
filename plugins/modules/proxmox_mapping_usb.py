#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_mapping_usb
short_description: Manage USB device mappings in Proxmox VE
version_added: "1.0.0"
description:
  - Create, update, or remove USB device mappings in Proxmox VE via the
    C(/cluster/mapping/usb) API endpoint.
  - USB mappings allow referencing hardware devices by logical name in VM
    configurations, making it portable across cluster nodes.
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
  name:
    description:
      - The logical name for the USB device mapping.
    type: str
    required: true
  description:
    description:
      - Description of the USB mapping.
    type: str
  map:
    description:
      - List of device mapping entries.
      - "Each entry is a string like C(id=1234:5678,node=pve1,path=1-2)."
    type: list
    elements: str
  state:
    description:
      - Whether the USB mapping should be present or absent.
    type: str
    choices: ['present', 'absent']
    default: present
author:
  - sfulmer
'''

EXAMPLES = r'''
- name: Create a USB device mapping
  stevefulme1.proxmox.proxmox_mapping_usb:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    name: yubikey
    description: "YubiKey security token"
    map:
      - "id=1050:0407,node=pve1,path=1-2"

- name: Update a USB mapping with multiple nodes
  stevefulme1.proxmox.proxmox_mapping_usb:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    name: usb_scanner
    map:
      - "id=04b8:0142,node=pve1,path=2-1"
      - "id=04b8:0142,node=pve2,path=1-3"

- name: Remove a USB mapping
  stevefulme1.proxmox.proxmox_mapping_usb:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    name: yubikey
    state: absent
'''

RETURN = r'''
name:
  description: The USB mapping name that was managed.
  returned: success
  type: str
  sample: "yubikey"
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def get_mapping(api, name):
    """Return USB mapping dict or None if not found."""
    try:
        return api.cluster.mapping.usb(name).get()
    except Exception:
        return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        description=dict(type='str'),
        map=dict(type='list', elements='str'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    proxmox = ProxmoxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module = proxmox.module
    params = module.params
    name = params['name']
    state = params['state']

    api = proxmox.get_api()
    existing = get_mapping(api, name)
    result = dict(name=name)

    if state == 'absent':
        if existing is None:
            module.exit_json(changed=False, **result)
        changed = True
        if not module.check_mode:
            try:
                api.cluster.mapping.usb(name).delete()
            except Exception as e:
                module.fail_json(
                    msg="Failed to delete USB mapping '%s': %s" % (name, str(e)))
        module.exit_json(changed=changed, **result)

    # state == present
    if existing is None:
        # Create
        if not params.get('map'):
            module.fail_json(msg="Parameter 'map' is required when creating a USB mapping.")
        changed = True
        if not module.check_mode:
            post_params = dict(id=name, map=params['map'])
            if params.get('description') is not None:
                post_params['description'] = params['description']
            try:
                api.cluster.mapping.usb.post(**post_params)
            except Exception as e:
                module.fail_json(
                    msg="Failed to create USB mapping '%s': %s" % (name, str(e)))
        module.exit_json(changed=changed, **result)

    # Update existing
    update_params = {}
    if params.get('description') is not None:
        if existing.get('description', '') != params['description']:
            update_params['description'] = params['description']
    if params.get('map') is not None:
        existing_map = existing.get('map', [])
        if isinstance(existing_map, str):
            existing_map = [existing_map]
        if sorted(existing_map) != sorted(params['map']):
            update_params['map'] = params['map']

    if not update_params:
        module.exit_json(changed=False, **result)

    changed = True
    if not module.check_mode:
        try:
            api.cluster.mapping.usb(name).put(**update_params)
        except Exception as e:
            module.fail_json(
                msg="Failed to update USB mapping '%s': %s" % (name, str(e)))

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
