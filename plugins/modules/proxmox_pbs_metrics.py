#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_metrics
short_description: Configure Proxmox Backup Server metrics export
description:
  - Create, update, or remove metrics server configurations on a Proxmox Backup Server.
  - Allows exporting PBS metrics to InfluxDB instances.
  - Uses the C(/config/metrics) API endpoint.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  name:
    description: Unique name for the metrics server configuration.
    type: str
    required: true
  type:
    description:
      - Type of metrics server.
      - Required when creating a new metrics configuration.
    type: str
    choices: ['influxdb-http', 'influxdb-udp']
  server:
    description:
      - Hostname or IP address of the metrics server.
      - Required when creating a new metrics configuration.
    type: str
  port:
    description: Port of the metrics server.
    type: int
  disable:
    description: Whether the metrics export is disabled.
    type: bool
  comment:
    description: Description for the metrics configuration.
    type: str
  state:
    description: Whether the metrics configuration should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Configure InfluxDB HTTP metrics export
  stevefulme1.proxmox.proxmox_pbs_metrics:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: influx-prod
    type: influxdb-http
    server: influxdb.example.com
    port: 8086
    comment: Production InfluxDB metrics
    state: present

- name: Configure InfluxDB UDP metrics export
  stevefulme1.proxmox.proxmox_pbs_metrics:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: influx-udp
    type: influxdb-udp
    server: influxdb.example.com
    port: 8089
    state: present

- name: Disable a metrics export
  stevefulme1.proxmox.proxmox_pbs_metrics:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: influx-prod
    type: influxdb-http
    server: influxdb.example.com
    disable: true
    state: present

- name: Remove a metrics configuration
  stevefulme1.proxmox.proxmox_pbs_metrics:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: influx-prod
    state: absent
'''

RETURN = r'''
name:
  description: The metrics configuration name that was managed.
  returned: always
  type: str
  sample: influx-prod
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        type=dict(type='str', choices=['influxdb-http', 'influxdb-udp']),
        server=dict(type='str'),
        port=dict(type='int'),
        disable=dict(type='bool'),
        comment=dict(type='str'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    name = params['name']
    state = params['state']

    try:
        metrics_list = api.config.metrics.get()
    except Exception as e:
        module.fail_json(msg="Failed to list metrics configurations: %s" % str(e))

    existing = None
    for m in metrics_list:
        if m.get('name') == name:
            existing = m
            break

    changed = False
    result = dict(name=name, changed=False)

    config_keys = ['type', 'server', 'port', 'disable', 'comment']

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.config.metrics(name).delete()
                except Exception as e:
                    module.fail_json(
                        msg="Failed to delete metrics configuration '%s': %s" % (name, str(e))
                    )
            changed = True
    else:
        config = {}
        for key in config_keys:
            if params.get(key) is not None:
                value = params[key]
                if isinstance(value, bool):
                    value = int(value)
                config[key] = value

        if existing:
            update_params = {}
            for key, value in config.items():
                # Skip 'type' on updates as it cannot be changed
                if key == 'type':
                    continue
                if str(existing.get(key, '')) != str(value):
                    update_params[key] = value
            if update_params:
                if not module.check_mode:
                    try:
                        api.config.metrics(name).put(**update_params)
                    except Exception as e:
                        module.fail_json(
                            msg="Failed to update metrics configuration '%s': %s" % (name, str(e))
                        )
                changed = True
        else:
            if not params.get('type'):
                module.fail_json(msg="'type' is required when creating a new metrics configuration.")
            if not params.get('server'):
                module.fail_json(msg="'server' is required when creating a new metrics configuration.")
            config['name'] = name
            if not module.check_mode:
                try:
                    api.config.metrics.post(**config)
                except Exception as e:
                    module.fail_json(
                        msg="Failed to create metrics configuration '%s': %s" % (name, str(e))
                    )
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
