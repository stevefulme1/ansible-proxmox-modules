#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_datastore_info
short_description: Query Proxmox Backup Server datastore information
description:
  - Retrieve configuration and status of datastores on a Proxmox Backup Server.
  - Uses the C(/config/datastore) and C(/admin/datastore/{store}/status) API endpoints.
  - This is an info module that does not modify state.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  name:
    description:
      - Name of a specific datastore to query.
      - If not specified, all datastores are returned.
    type: str
  limit:
    description:
      - Maximum number of results to return.
    type: int
    default: 100
  offset:
    description:
      - Number of results to skip for pagination.
    type: int
    default: 0
  max_results:
    description:
      - Maximum total results to return.
    type: int
    default: 1000
'''

EXAMPLES = r'''
- name: Get all PBS datastore information
  stevefulme1.proxmox.proxmox_pbs_datastore_info:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
  register: ds_info

- name: Get a specific datastore with status
  stevefulme1.proxmox.proxmox_pbs_datastore_info:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: backups
  register: ds_info

- name: Display datastore details
  ansible.builtin.debug:
    var: ds_info.datastores
'''

RETURN = r'''
datastores:
  description: List of datastore configurations.
  returned: always
  type: list
  elements: dict
status:
  description: Status information for the requested datastore (when name is specified).
  returned: when name is specified
  type: dict
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        limit=dict(type='int', default=100),
        offset=dict(type='int', default=0),
        max_results=dict(type='int', default=1000),
        name=dict(type='str'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    result = dict(changed=False)
    name = params.get('name')

    try:
        datastores = api.config.datastore.get()
    except Exception as e:
        module.fail_json(msg="Failed to list datastores: %s" % str(e))

    if name:
        filtered = [ds for ds in datastores if ds.get('name') == name]
        if not filtered:
            module.fail_json(msg="Datastore '%s' not found." % name)
        result['datastores'] = filtered

        try:
            status = api.admin.datastore(name).status.get()
            result['status'] = status
        except Exception as e:
            module.fail_json(msg="Failed to get status for datastore '%s': %s" % (name, str(e)))
    else:
        result['datastores'] = datastores

    module.exit_json(**result)


if __name__ == '__main__':
    main()
