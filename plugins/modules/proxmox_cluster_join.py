#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_cluster_join
short_description: Join a node to an existing Proxmox VE cluster
description:
  - Join the current Proxmox VE node to an existing cluster.
  - This is a one-way operation and cannot be undone without reinstalling.
  - The module verifies the node is not already part of a multi-node cluster before attempting to join.
  - Check mode is not supported because this operation is destructive and irreversible.
version_added: "1.1.0"
author:
  - sfulmer
options:
  hostname:
    description:
      - The hostname or IP address of an existing cluster node to join.
    type: str
    required: true
  password:
    description:
      - The root password of the existing cluster node.
    type: str
    required: true
  fingerprint:
    description:
      - The SSL certificate fingerprint of the existing cluster node.
      - If not provided, the certificate will not be verified.
    type: str
  force:
    description:
      - Force joining even if the node is already part of a cluster.
      - Use with caution as this can cause data loss.
    type: bool
    default: false
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Join a node to the cluster
  stevefulme1.proxmox.proxmox_cluster_join:
    api_host: new-node.example.com
    api_user: root@pam
    api_password: local_secret
    hostname: existing-node.example.com
    password: cluster_root_password
    fingerprint: "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99"

- name: Force-join a node to the cluster
  stevefulme1.proxmox.proxmox_cluster_join:
    api_host: new-node.example.com
    api_user: root@pam
    api_password: local_secret
    hostname: existing-node.example.com
    password: cluster_root_password
    force: true
'''

RETURN = r'''
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "Node successfully joined cluster via existing-node.example.com."
cluster_status:
  description: Cluster status before join attempt.
  type: list
  returned: always
  elements: dict
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            hostname=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            fingerprint=dict(type='str'),
            force=dict(type='bool', default=False),
        ),
        supports_check_mode=False,
    )

    hostname = module.params['hostname']
    password = module.params['password']
    fingerprint = module.params.get('fingerprint')
    force = module.params['force']

    api = module.get_api()

    # Check if the node is already in a multi-node cluster
    try:
        cluster_status = api.cluster.status.get()
    except Exception as e:
        module.fail_json(msg="Failed to get cluster status: {0}".format(e))

    node_count = sum(1 for entry in cluster_status if entry.get('type') == 'node')

    if node_count > 1 and not force:
        module.fail_json(
            msg="Node is already part of a cluster with {0} nodes. Use force=true to override.".format(node_count),
            cluster_status=cluster_status,
        )

    # Build join parameters
    join_params = dict(
        hostname=hostname,
        password=password,
    )
    if fingerprint:
        join_params['fingerprint'] = fingerprint
    if force:
        join_params['force'] = 1

    try:
        api.cluster.join.post(**join_params)
    except Exception as e:
        module.fail_json(msg="Failed to join cluster via '{0}': {1}".format(hostname, e), cluster_status=cluster_status)

    module.exit_json(
        changed=True,
        msg="Node successfully joined cluster via {0}.".format(hostname),
        cluster_status=cluster_status,
    )


if __name__ == '__main__':
    main()
