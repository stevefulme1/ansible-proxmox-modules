#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_cluster_metrics
short_description: Configure Proxmox VE external metrics server
description:
  - Manage external metrics server configuration in Proxmox VE.
  - Uses the C(/cluster/metrics/server) API endpoints to create, update, and delete
    metrics server entries.
  - Supports Graphite and InfluxDB backends.
version_added: "1.0.0"
author:
  - sfulmer
options:
  name:
    description:
      - The unique identifier for this metrics server configuration.
    type: str
    required: true
  type:
    description:
      - The type of metrics server backend.
    type: str
    choices: ['graphite', 'influxdb']
  server:
    description:
      - The hostname or IP address of the metrics server.
    type: str
  port:
    description:
      - The port number of the metrics server.
    type: int
  disable:
    description:
      - Whether to disable this metrics server configuration.
    type: bool
  mtu:
    description:
      - MTU for the metrics UDP packets.
    type: int
  path:
    description:
      - The root path for InfluxDB metrics.
      - Only applicable when I(type=influxdb).
    type: str
  protocol:
    description:
      - The protocol to use for sending metrics.
    type: str
  timeout:
    description:
      - Timeout in seconds for the metrics connection.
    type: int
  state:
    description:
      - Whether the metrics server configuration should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Configure InfluxDB metrics server
  stevefulme1.proxmox.proxmox_cluster_metrics:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    name: influx1
    type: influxdb
    server: influxdb.example.com
    port: 8089
    path: proxmox

- name: Configure Graphite metrics server
  stevefulme1.proxmox.proxmox_cluster_metrics:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    name: graphite1
    type: graphite
    server: graphite.example.com
    port: 2003

- name: Remove a metrics server configuration
  stevefulme1.proxmox.proxmox_cluster_metrics:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    name: influx1
    state: absent
'''

RETURN = r'''
metrics_server:
  description: The metrics server configuration after changes.
  type: dict
  returned: success and state is present
name:
  description: The name of the metrics server configuration.
  type: str
  returned: always
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            type=dict(type='str', choices=['graphite', 'influxdb']),
            server=dict(type='str'),
            port=dict(type='int'),
            disable=dict(type='bool'),
            mtu=dict(type='int'),
            path=dict(type='str'),
            protocol=dict(type='str'),
            timeout=dict(type='int'),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
        ),
        required_if=[
            ('state', 'present', ['type', 'server', 'port']),
        ],
        supports_check_mode=True,
    )

    name = module.params['name']
    state = module.params['state']

    # Get list of existing metrics servers
    try:
        existing_servers = module.proxmox_api.cluster.metrics.server.get()
    except Exception as e:
        module.fail_json(msg="Failed to get metrics servers: {0}".format(e))

    current = None
    for srv in existing_servers:
        if srv.get('id') == name or srv.get('name') == name:
            current = srv
            break

    if state == 'absent':
        if current is None:
            module.exit_json(changed=False, name=name)

        if module.check_mode:
            module.exit_json(changed=True, name=name)

        try:
            module.proxmox_api.cluster.metrics.server(name).delete()
        except Exception as e:
            module.fail_json(msg="Failed to delete metrics server '{0}': {1}".format(name, e))

        module.exit_json(changed=True, name=name)

    # state == present
    config_keys = ['type', 'server', 'port', 'disable', 'mtu', 'path', 'protocol', 'timeout']
    desired = {}
    for key in config_keys:
        value = module.params.get(key)
        if value is not None:
            desired[key] = value

    if current is not None:
        # Check if update is needed
        changes = {}
        for key, desired_value in desired.items():
            current_value = current.get(key)
            if key == 'disable':
                current_bool = bool(int(current_value)) if current_value is not None else False
                if desired_value != current_bool:
                    changes[key] = int(desired_value)
            elif str(desired_value) != str(current_value or ''):
                changes[key] = desired_value

        if not changes:
            module.exit_json(changed=False, name=name, metrics_server=current)

        if module.check_mode:
            module.exit_json(changed=True, name=name, metrics_server=current)

        try:
            module.proxmox_api.cluster.metrics.server(name).put(**changes)
        except Exception as e:
            module.fail_json(
                msg="Failed to update metrics server '{0}': {1}".format(name, e)
            )
    else:
        # Create new metrics server
        if module.check_mode:
            module.exit_json(changed=True, name=name)

        create_params = dict(desired)
        if 'disable' in create_params:
            create_params['disable'] = int(create_params['disable'])

        try:
            module.proxmox_api.cluster.metrics.server(name).post(**create_params)
        except Exception as e:
            module.fail_json(
                msg="Failed to create metrics server '{0}': {1}".format(name, e)
            )

    # Fetch updated configuration
    try:
        updated_servers = module.proxmox_api.cluster.metrics.server.get()
        updated = None
        for srv in updated_servers:
            if srv.get('id') == name or srv.get('name') == name:
                updated = srv
                break
    except Exception:
        updated = None

    module.exit_json(changed=True, name=name, metrics_server=updated)


if __name__ == '__main__':
    main()
