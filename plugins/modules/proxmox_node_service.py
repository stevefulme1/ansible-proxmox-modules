#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_service
short_description: Manage services on Proxmox VE nodes
version_added: "1.0.0"
description:
  - Start, stop, restart, or reload services on Proxmox VE nodes
    via the C(/nodes/{node}/services/{service}) API endpoint.
  - Query service status with C(action=status).
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
  service:
    description:
      - The service name to manage.
      - "Examples: C(pvedaemon), C(pveproxy), C(pvestatd), C(ceph), C(corosync)."
    type: str
    required: true
  action:
    description:
      - The action to perform on the service.
      - C(status) returns the current service status without making changes.
    type: str
    required: true
    choices: ['start', 'stop', 'restart', 'reload', 'status']
author:
  - sfulmer
'''

EXAMPLES = r'''
- name: Restart pvedaemon
  stevefulme1.proxmox.proxmox_node_service:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    service: pvedaemon
    action: restart

- name: Check pveproxy status
  stevefulme1.proxmox.proxmox_node_service:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    service: pveproxy
    action: status
  register: svc_status

- name: Stop ceph service
  stevefulme1.proxmox.proxmox_node_service:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    service: ceph
    action: stop
'''

RETURN = r'''
service:
  description: The service name that was managed.
  returned: success
  type: str
  sample: "pvedaemon"
action:
  description: The action that was performed.
  returned: success
  type: str
  sample: "restart"
status:
  description: Service status information (when action is status).
  returned: when action is status
  type: dict
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    argument_spec = dict(
        node=dict(type='str', required=True),
        service=dict(type='str', required=True),
        action=dict(type='str', required=True,
                    choices=['start', 'stop', 'restart', 'reload', 'status']),
    )

    proxmox = ProxmoxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module = proxmox.module
    params = module.params
    node = params['node']
    service = params['service']
    action = params['action']

    api = proxmox.get_api()
    result = dict(service=service, action=action)

    if action == 'status':
        try:
            status = api.nodes(node).services(service).state.get()
        except Exception as e:
            module.fail_json(
                msg="Failed to get status of service '%s' on node '%s': %s"
                % (service, node, str(e)))
        result['status'] = status
        module.exit_json(changed=False, **result)

    # For start/stop/restart/reload, always report changed
    changed = True
    if not module.check_mode:
        try:
            svc_api = api.nodes(node).services(service)
            if action == 'start':
                svc_api.start.post()
            elif action == 'stop':
                svc_api.stop.post()
            elif action == 'restart':
                svc_api.restart.post()
            elif action == 'reload':
                svc_api.reload.post()
        except Exception as e:
            module.fail_json(
                msg="Failed to %s service '%s' on node '%s': %s"
                % (action, service, node, str(e)))

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
