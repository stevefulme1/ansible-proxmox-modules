#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_cluster_info
short_description: Gather Proxmox VE cluster information
description:
  - Retrieve cluster status, resources, and configuration from a Proxmox VE cluster.
  - This is an info module that does not modify state.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  type:
    description:
      - Filter resources by type.
      - If not specified, all resources are returned.
    type: str
    choices: ['vm', 'storage', 'node']
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
- name: Get all cluster information
  stevefulme1.proxmox.proxmox_cluster_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
  register: cluster_info

- name: Get only VM resources
  stevefulme1.proxmox.proxmox_cluster_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    type: vm
  register: vm_info

- name: Display cluster name
  ansible.builtin.debug:
    var: cluster_info.cluster_name
'''

RETURN = r'''
cluster_name:
  description: The name of the Proxmox cluster.
  returned: always
  type: str
  sample: mycluster
cluster_status:
  description: Full cluster status information.
  returned: always
  type: list
  elements: dict
nodes:
  description: List of cluster nodes with status.
  returned: always
  type: list
  elements: dict
quorate:
  description: Whether the cluster has quorum.
  returned: always
  type: bool
  sample: true
version:
  description: Proxmox VE version information.
  returned: when available
  type: dict
resources:
  description: Cluster resources, optionally filtered by type.
  returned: always
  type: list
  elements: dict
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        limit=dict(type='int', default=100),
        offset=dict(type='int', default=0),
        max_results=dict(type='int', default=1000),
        type=dict(type='str', choices=['vm', 'storage', 'node']),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    result = dict(changed=False)

    # Get cluster status
    try:
        status = api.cluster.status.get()
    except Exception as e:
        module.fail_json(msg="Failed to get cluster status: %s" % str(e))

    result['cluster_status'] = status

    # Extract cluster name and nodes
    cluster_name = ''
    nodes = []
    quorate = False
    for item in status:
        if item.get('type') == 'cluster':
            cluster_name = item.get('name', '')
            quorate = bool(item.get('quorate', 0))
        elif item.get('type') == 'node':
            nodes.append(item)

    result['cluster_name'] = cluster_name
    result['nodes'] = nodes
    result['quorate'] = quorate

    # Get resources
    try:
        resource_params = dict()
        if params.get('type'):
            resource_params['type'] = params['type']
        resources = api.cluster.resources.get(**resource_params)
    except Exception as e:
        module.fail_json(msg="Failed to get cluster resources: %s" % str(e))

    result['resources'] = resources

    # Get version info
    try:
        version = api.version.get()
        result['version'] = version
    except Exception:
        result['version'] = {}

    module.exit_json(**result)


if __name__ == '__main__':
    main()
