#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_agent
short_description: Execute commands via QEMU guest agent in Proxmox VE
description:
  - Interact with a running VM via the QEMU guest agent.
  - Supports querying system information, reading/writing files, and executing commands.
  - This is an action module and is not fully idempotent.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox node the VM resides on.
    type: str
    required: true
  vmid:
    description:
      - The VM ID.
    type: int
    required: true
  command:
    description:
      - The guest agent command to execute.
    type: str
    required: true
    choices:
      - ping
      - get-osinfo
      - get-host-name
      - get-memory-blocks
      - get-memory-block-info
      - get-vcpus
      - get-fsinfo
      - get-users-logged-in
      - get-timezone
      - network-get-interfaces
      - file-read
      - file-write
      - exec
  file_path:
    description:
      - The file path for C(file-read) and C(file-write) commands.
    type: str
  file_content:
    description:
      - The content to write for the C(file-write) command.
    type: str
  exec_command:
    description:
      - The command string to execute for the C(exec) command.
    type: str
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Ping the guest agent
  stevefulme1.proxmox.proxmox_vm_agent:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    command: ping

- name: Get OS information
  stevefulme1.proxmox.proxmox_vm_agent:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    command: get-osinfo
  register: osinfo

- name: Read a file from the VM
  stevefulme1.proxmox.proxmox_vm_agent:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    command: file-read
    file_path: /etc/hostname

- name: Write a file to the VM
  stevefulme1.proxmox.proxmox_vm_agent:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    command: file-write
    file_path: /tmp/hello.txt
    file_content: "Hello, World!"

- name: Execute a command in the VM
  stevefulme1.proxmox.proxmox_vm_agent:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    command: exec
    exec_command: "uname -a"
'''

RETURN = r'''
result:
  description: The response from the guest agent command.
  type: dict
  returned: always
  sample:
    hostname: myvm
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "Guest agent command 'ping' executed successfully."
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


# Commands that only read state and never change anything
READ_ONLY_COMMANDS = frozenset([
    'ping', 'get-osinfo', 'get-host-name', 'get-memory-blocks',
    'get-memory-block-info', 'get-vcpus', 'get-fsinfo',
    'get-users-logged-in', 'get-timezone', 'network-get-interfaces',
    'file-read',
])


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            vmid=dict(type='int', required=True),
            command=dict(
                type='str', required=True,
                choices=[
                    'ping', 'get-osinfo', 'get-host-name',
                    'get-memory-blocks', 'get-memory-block-info',
                    'get-vcpus', 'get-fsinfo', 'get-users-logged-in',
                    'get-timezone', 'network-get-interfaces',
                    'file-read', 'file-write', 'exec',
                ],
            ),
            file_path=dict(type='str'),
            file_content=dict(type='str'),
            exec_command=dict(type='str'),
        ),
        required_if=[
            ('command', 'file-read', ['file_path']),
            ('command', 'file-write', ['file_path', 'file_content']),
            ('command', 'exec', ['exec_command']),
        ],
        supports_check_mode=True,
    )

    node = module.params['node']
    vmid = module.params['vmid']
    command = module.params['command']
    file_path = module.params.get('file_path')
    file_content = module.params.get('file_content')
    exec_command = module.params.get('exec_command')

    base_url = 'nodes/{0}/qemu/{1}/agent'.format(node, vmid)
    changed = command not in READ_ONLY_COMMANDS

    if module.check_mode and changed:
        module.exit_json(
            changed=True,
            result={},
            msg="Guest agent command '{0}' would be executed.".format(
                command,
            ),
        )

    if command == 'file-read':
        result = module.proxmox_request(
            'GET',
            '{0}/file-read'.format(base_url),
            params={'file': file_path},
        )
    elif command == 'file-write':
        result = module.proxmox_request(
            'POST',
            '{0}/file-write'.format(base_url),
            data={'file': file_path, 'content': file_content},
        )
    elif command == 'exec':
        result = module.proxmox_request(
            'POST',
            '{0}/exec'.format(base_url),
            data={'command': exec_command},
        )
    else:
        result = module.proxmox_request(
            'GET', '{0}/{1}'.format(base_url, command),
        )

    module.exit_json(
        changed=changed,
        result=result if result else {},
        msg="Guest agent command '{0}' executed successfully.".format(
            command,
        ),
    )


if __name__ == '__main__':
    main()
