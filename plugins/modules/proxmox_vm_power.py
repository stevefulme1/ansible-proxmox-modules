#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_power
short_description: Control power state of a QEMU/KVM VM in Proxmox VE
description:
  - Start, stop, restart, shutdown, suspend, or resume a QEMU/KVM virtual machine.
  - Idempotent — will not attempt to start an already running VM, stop an already stopped VM, etc.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node where the VM resides.
    type: str
    required: true
  vmid:
    description:
      - The VM ID to control.
    type: int
    required: true
  state:
    description:
      - The desired power state of the VM.
      - C(started) starts the VM if it is not running.
      - C(stopped) performs a hard stop (power off) if the VM is running.
      - C(restarted) resets the VM (hard reboot). The VM must be running.
      - C(shutdown) sends a graceful ACPI shutdown signal.
      - C(suspended) suspends the VM.
      - C(resumed) resumes a suspended VM.
    type: str
    required: true
    choices:
      - started
      - stopped
      - restarted
      - shutdown
      - suspended
      - resumed
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Start a VM
  stevefulme1.proxmox.proxmox_vm_power:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    state: started

- name: Gracefully shutdown a VM
  stevefulme1.proxmox.proxmox_vm_power:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    state: shutdown

- name: Hard stop a VM
  stevefulme1.proxmox.proxmox_vm_power:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    state: stopped
'''

RETURN = r'''
vmid:
  description: The VM ID that was controlled.
  type: int
  returned: always
  sample: 100
status:
  description: The current VM status after the operation.
  type: str
  returned: always
  sample: running
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "VM 100 started successfully."
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


def get_vm_status(api, node, vmid):
    """Get the current status of a VM."""
    try:
        status = api.nodes(node).qemu(vmid).status.current.get()
        return status.get('status', 'unknown')
    except Exception:
        return None


def main():
    module_args = dict(
        node=dict(type='str', required=True),
        vmid=dict(type='int', required=True),
        state=dict(
            type='str', required=True,
            choices=['started', 'stopped', 'restarted', 'shutdown', 'suspended', 'resumed'],
        ),
    )

    proxmox = ProxmoxModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    node = params['node']
    vmid = params['vmid']
    desired_state = params['state']

    current_status = get_vm_status(api, node, vmid)
    if current_status is None:
        module.fail_json(msg="VM %d not found on node %s." % (vmid, node))

    changed = False
    action_msg = ""

    if desired_state == 'started':
        if current_status != 'running':
            changed = True
            action_msg = "VM %d started successfully." % vmid
            if not module.check_mode:
                try:
                    api.nodes(node).qemu(vmid).status.start.post()
                except Exception as e:
                    module.fail_json(msg="Failed to start VM %d: %s" % (vmid, str(e)))
        else:
            action_msg = "VM %d is already running." % vmid

    elif desired_state == 'stopped':
        if current_status != 'stopped':
            changed = True
            action_msg = "VM %d stopped successfully." % vmid
            if not module.check_mode:
                try:
                    api.nodes(node).qemu(vmid).status.stop.post()
                except Exception as e:
                    module.fail_json(msg="Failed to stop VM %d: %s" % (vmid, str(e)))
        else:
            action_msg = "VM %d is already stopped." % vmid

    elif desired_state == 'restarted':
        changed = True
        action_msg = "VM %d restarted successfully." % vmid
        if not module.check_mode:
            try:
                api.nodes(node).qemu(vmid).status.reset.post()
            except Exception as e:
                module.fail_json(msg="Failed to restart VM %d: %s" % (vmid, str(e)))

    elif desired_state == 'shutdown':
        if current_status == 'running':
            changed = True
            action_msg = "VM %d shutdown signal sent." % vmid
            if not module.check_mode:
                try:
                    api.nodes(node).qemu(vmid).status.shutdown.post()
                except Exception as e:
                    module.fail_json(msg="Failed to shutdown VM %d: %s" % (vmid, str(e)))
        else:
            action_msg = "VM %d is not running, no shutdown needed." % vmid

    elif desired_state == 'suspended':
        if current_status == 'running':
            changed = True
            action_msg = "VM %d suspended successfully." % vmid
            if not module.check_mode:
                try:
                    api.nodes(node).qemu(vmid).status.suspend.post()
                except Exception as e:
                    module.fail_json(msg="Failed to suspend VM %d: %s" % (vmid, str(e)))
        else:
            action_msg = "VM %d is not running, cannot suspend." % vmid

    elif desired_state == 'resumed':
        if current_status == 'paused':
            changed = True
            action_msg = "VM %d resumed successfully." % vmid
            if not module.check_mode:
                try:
                    api.nodes(node).qemu(vmid).status.resume.post()
                except Exception as e:
                    module.fail_json(msg="Failed to resume VM %d: %s" % (vmid, str(e)))
        else:
            action_msg = "VM %d is not suspended, no resume needed." % vmid

    # Get updated status if not in check mode
    if not module.check_mode:
        final_status = get_vm_status(api, node, vmid) or current_status
    else:
        final_status = current_status

    module.exit_json(changed=changed, vmid=vmid, status=final_status, msg=action_msg)


if __name__ == '__main__':
    main()
