#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_tag
short_description: Manage VM and container tags in Proxmox VE
description:
  - Add or remove tags on virtual machines and LXC containers in Proxmox VE.
  - Tags are stored as a semicolon-separated string in the VM/container config.
  - Compares current tags and only updates when changes are needed.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox node the VM or container resides on.
    type: str
    required: true
  vmid:
    description:
      - The VM or container ID.
    type: int
    required: true
  vm_type:
    description:
      - Whether the target is a QEMU VM or an LXC container.
    type: str
    default: qemu
    choices:
      - qemu
      - lxc
  tags:
    description:
      - List of tags to manage.
    type: list
    elements: str
    required: true
  state:
    description:
      - Whether the specified tags should be present or absent.
      - When C(present), the listed tags are added (merged with existing tags).
      - When C(absent), the listed tags are removed from the current set.
    type: str
    default: present
    choices:
      - present
      - absent
extends_documentation_fragment:
  - sfulmer.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Add tags to a VM
  sfulmer.proxmox.proxmox_tag:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    tags:
      - production
      - web
    state: present

- name: Remove a tag from an LXC container
  sfulmer.proxmox.proxmox_tag:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 200
    vm_type: lxc
    tags:
      - deprecated
    state: absent

- name: Set tags on a VM (existing tags are preserved)
  sfulmer.proxmox.proxmox_tag:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    tags:
      - staging
      - database
    state: present
'''

RETURN = r'''
vmid:
  description: The VM or container ID whose tags were managed.
  type: int
  returned: always
  sample: 100
tags:
  description: The resulting set of tags after the operation.
  type: list
  elements: str
  returned: always
  sample:
    - production
    - web
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "Tags updated for VM 100."
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


def _parse_tags(tag_string):
    """Parse a semicolon-separated tag string into a set."""
    if not tag_string:
        return set()
    return set(
        t.strip() for t in tag_string.split(';') if t.strip()
    )


def _tags_to_string(tags):
    """Convert a set of tags to a sorted semicolon-separated string."""
    return ';'.join(sorted(tags))


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            vmid=dict(type='int', required=True),
            vm_type=dict(
                type='str', default='qemu', choices=['qemu', 'lxc'],
            ),
            tags=dict(type='list', elements='str', required=True),
            state=dict(
                type='str', default='present',
                choices=['present', 'absent'],
            ),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    vmid = module.params['vmid']
    vm_type = module.params['vm_type']
    desired_tags = set(module.params['tags'])
    state = module.params['state']

    config_path = 'nodes/{0}/{1}/{2}/config'.format(node, vm_type, vmid)

    current_config = module.proxmox_request('GET', config_path)
    current_tags = _parse_tags(current_config.get('tags', ''))

    if state == 'present':
        new_tags = current_tags | desired_tags
    else:
        new_tags = current_tags - desired_tags

    changed = new_tags != current_tags

    if changed and not module.check_mode:
        tag_string = _tags_to_string(new_tags)
        module.proxmox_request(
            'PUT', config_path, data={'tags': tag_string},
        )

    msg = (
        "Tags updated for VM {0}.".format(vmid)
        if changed
        else "Tags already up to date for VM {0}.".format(vmid)
    )

    module.exit_json(
        changed=changed,
        vmid=vmid,
        tags=sorted(list(new_tags)),
        msg=msg,
    )


if __name__ == '__main__':
    main()
