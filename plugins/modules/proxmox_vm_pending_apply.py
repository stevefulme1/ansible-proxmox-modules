#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_pending_apply
short_description: Apply pending VM configuration changes by rebooting
version_added: "1.0.0"
description:
  - Check for pending configuration changes on a QEMU VM and apply them by
    triggering a reboot via C(POST /nodes/{node}/qemu/{vmid}/status/reboot).
  - If there are no pending changes, the module reports C(changed=False)
    and does not reboot the VM.
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
  vmid:
    description: The VM ID.
    type: int
    required: true
  timeout:
    description:
      - Timeout in seconds to wait for the reboot task to complete.
      - Set to 0 to not wait.
    type: int
    default: 0
author:
  - sfulmer
'''

EXAMPLES = r'''
- name: Apply pending VM config changes
  sfulmer.proxmox.proxmox_vm_pending_apply:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100

- name: Apply pending changes and wait up to 120 seconds
  sfulmer.proxmox.proxmox_vm_pending_apply:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 101
    timeout: 120
'''

RETURN = r'''
vmid:
  description: The VM ID that was managed.
  returned: success
  type: int
  sample: 100
pending:
  description: List of pending configuration changes found.
  returned: success
  type: list
  elements: dict
upid:
  description: The task UPID for the reboot operation.
  returned: when rebooted, not check_mode
  type: str
'''

import time
from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    argument_spec = dict(
        node=dict(type='str', required=True),
        vmid=dict(type='int', required=True),
        timeout=dict(type='int', default=0),
    )

    proxmox = ProxmoxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module = proxmox.module
    params = module.params
    node = params['node']
    vmid = params['vmid']
    timeout = params['timeout']

    api = proxmox.get_api()
    result = dict(vmid=vmid)

    # Check for pending changes
    try:
        pending = api.nodes(node).qemu(vmid).pending.get()
    except Exception as e:
        module.fail_json(
            msg="Failed to query pending config for VM %d on node '%s': %s"
            % (vmid, node, str(e)))

    # Filter to only entries that have a 'pending' key (actual pending changes)
    actual_pending = [p for p in pending if 'pending' in p or 'delete' in p]
    result['pending'] = actual_pending

    if not actual_pending:
        module.exit_json(changed=False, **result)

    changed = True
    if not module.check_mode:
        try:
            upid = api.nodes(node).qemu(vmid).status.reboot.post()
            result['upid'] = upid
        except Exception as e:
            module.fail_json(
                msg="Failed to reboot VM %d on node '%s': %s"
                % (vmid, node, str(e)))

        # Wait for task if timeout > 0
        if timeout > 0 and upid:
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    task_status = api.nodes(node).tasks(upid).status.get()
                    if task_status.get('status') == 'stopped':
                        if task_status.get('exitstatus') != 'OK':
                            module.fail_json(
                                msg="Reboot task for VM %d failed: %s"
                                % (vmid, task_status.get('exitstatus', 'unknown')),
                                **result)
                        break
                except Exception:
                    pass
                time.sleep(2)
            else:
                module.fail_json(
                    msg="Timed out waiting for reboot task of VM %d after %d seconds."
                    % (vmid, timeout), **result)

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
