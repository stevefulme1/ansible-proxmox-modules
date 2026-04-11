#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_namespace
short_description: Manage Proxmox Backup Server datastore namespaces
description:
  - Create or remove namespaces within a Proxmox Backup Server datastore.
  - Uses the C(/admin/datastore/{store}/namespace) API endpoint.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  store:
    description: The datastore name containing the namespace.
    type: str
    required: true
  name:
    description:
      - The namespace path (e.g. C(project/sub)).
      - Nested namespaces use forward slashes as separators.
    type: str
    required: true
  state:
    description: Whether the namespace should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create a namespace in a datastore
  sfulmer.proxmox.proxmox_pbs_namespace:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    store: backups
    name: project/production
    state: present

- name: Remove a namespace
  sfulmer.proxmox.proxmox_pbs_namespace:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    store: backups
    name: project/staging
    state: absent
'''

RETURN = r'''
store:
  description: The datastore name.
  returned: always
  type: str
  sample: backups
name:
  description: The namespace path that was managed.
  returned: always
  type: str
  sample: project/production
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        store=dict(type='str', required=True),
        name=dict(type='str', required=True),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    store = params['store']
    name = params['name']
    state = params['state']

    # List existing namespaces
    try:
        namespaces = api.admin.datastore(store).namespace.get()
    except Exception as e:
        module.fail_json(msg="Failed to list namespaces for datastore '%s': %s" % (store, str(e)))

    existing = None
    for ns in namespaces:
        if ns.get('ns') == name:
            existing = ns
            break

    changed = False
    result = dict(store=store, name=name, changed=False)

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.admin.datastore(store).namespace.delete(ns=name)
                except Exception as e:
                    module.fail_json(
                        msg="Failed to delete namespace '%s' from datastore '%s': %s" % (name, store, str(e))
                    )
            changed = True
    else:
        if not existing:
            if not module.check_mode:
                try:
                    api.admin.datastore(store).namespace.post(name=name)
                except Exception as e:
                    module.fail_json(
                        msg="Failed to create namespace '%s' in datastore '%s': %s" % (name, store, str(e))
                    )
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
