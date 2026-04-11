#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_storage_content
short_description: Manage storage content in Proxmox VE
description:
  - Upload, or delete disk images, ISOs, and templates on Proxmox VE storage.
  - Uses the C(/nodes/{node}/storage/{storage}/content) API endpoint.
  - For uploads, the source file must exist on the Ansible controller and will be transferred via multipart form upload.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node name.
    type: str
    required: true
  storage:
    description:
      - The storage identifier.
    type: str
    required: true
  content_type:
    description:
      - The content type of the file.
    type: str
    choices: ['iso', 'vztmpl', 'images', 'rootdir', 'snippets']
  filename:
    description:
      - The filename (as it appears in Proxmox storage).
      - Required when I(state=absent) to identify the content to delete.
      - For uploads, derived from the source path basename if not specified.
    type: str
  source:
    description:
      - Local path on the Ansible controller of the file to upload.
      - Required when I(state=present).
    type: path
  state:
    description:
      - Whether the content should be present or absent.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Upload an ISO to storage
  sfulmer.proxmox.proxmox_storage_content:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    storage: local
    content_type: iso
    source: /tmp/ubuntu-22.04.iso
    state: present

- name: Delete an ISO from storage
  sfulmer.proxmox.proxmox_storage_content:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    storage: local
    content_type: iso
    filename: ubuntu-22.04.iso
    state: absent

- name: Upload a container template
  sfulmer.proxmox.proxmox_storage_content:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    storage: local
    content_type: vztmpl
    source: /tmp/debian-12-standard_12.2-1_amd64.tar.zst
    state: present
'''

RETURN = r'''
volid:
  description: The volume ID of the uploaded or identified content.
  returned: success
  type: str
  sample: "local:iso/ubuntu-22.04.iso"
'''

import os
from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def find_content(api, node, storage, content_type, filename):
    """Search for a file in storage content and return its volid or None."""
    try:
        params = {}
        if content_type:
            params['content'] = content_type
        contents = api.nodes(node).storage(storage).content.get(**params)
        for item in contents:
            volid = item.get('volid', '')
            if filename in volid:
                return item
        return None
    except Exception:
        return None


def main():
    module_args = dict(
        node=dict(type='str', required=True),
        storage=dict(type='str', required=True),
        content_type=dict(type='str', choices=['iso', 'vztmpl', 'images', 'rootdir', 'snippets']),
        filename=dict(type='str'),
        source=dict(type='path'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    proxmox = ProxmoxModule(
        argument_spec=module_args,
        required_if=[
            ('state', 'present', ['source', 'content_type']),
            ('state', 'absent', ['filename']),
        ],
    )
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    node = params['node']
    storage = params['storage']
    content_type = params.get('content_type')
    filename = params.get('filename')
    source = params.get('source')
    state = params['state']
    changed = False
    result = dict()

    # Derive filename from source if not specified
    if source and not filename:
        filename = os.path.basename(source)

    if state == 'absent':
        existing = find_content(api, node, storage, content_type, filename)
        if existing is not None:
            changed = True
            if not module.check_mode:
                volid = existing['volid']
                try:
                    api.nodes(node).storage(storage).content(volid).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete content '%s': %s" % (filename, str(e)))
            result['volid'] = existing.get('volid', '')
        module.exit_json(changed=changed, **result)

    # state == present
    existing = find_content(api, node, storage, content_type, filename)
    if existing is not None:
        result['volid'] = existing['volid']
        module.exit_json(changed=False, **result)

    # Upload the file
    if not os.path.isfile(source):
        module.fail_json(msg="Source file not found: %s" % source)

    changed = True
    if not module.check_mode:
        try:
            with open(source, 'rb') as fh:
                upload_result = api.nodes(node).storage(storage).upload.post(
                    content=content_type,
                    filename=fh,
                )
            result['volid'] = "%s:%s/%s" % (storage, content_type, filename)
            result['upid'] = upload_result
        except Exception as e:
            module.fail_json(msg="Failed to upload '%s': %s" % (source, str(e)))
    else:
        result['volid'] = "%s:%s/%s" % (storage, content_type, filename)

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
