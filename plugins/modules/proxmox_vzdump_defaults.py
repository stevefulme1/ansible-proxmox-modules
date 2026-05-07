#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vzdump_defaults
short_description: Manage default vzdump backup settings in Proxmox VE
version_added: "1.0.0"
description:
  - Configure default vzdump backup settings at the cluster or node level.
  - Uses C(/nodes/{node}/vzdump/defaults) when C(node) is specified,
    otherwise uses C(/cluster/options) for cluster-wide settings.
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
    description:
      - Target Proxmox VE node name for node-level defaults.
      - If omitted, cluster-level defaults are managed.
    type: str
  bwlimit:
    description: I/O bandwidth limit in KB/s.
    type: int
  compress:
    description: Compression algorithm to use for backups.
    type: str
    choices: ['0', 'gzip', 'lzo', 'zstd']
  dumpdir:
    description: Store resulting files in this directory.
    type: str
  ionice:
    description: Set I/O nice priority (0-8).
    type: int
  lockwait:
    description: Maximum time (in minutes) to wait for the global lock.
    type: int
  mailnotification:
    description: When to send email notifications about backup status.
    type: str
    choices: ['always', 'failure']
  mailto:
    description: Comma-separated list of email addresses for notifications.
    type: str
  maxfiles:
    description: Maximum number of backup files per guest.
    type: int
  mode:
    description: Backup mode.
    type: str
    choices: ['snapshot', 'suspend', 'stop']
  pigz:
    description:
      - Use pigz instead of gzip. Value is the number of threads (0 uses half of cores).
    type: int
  tmpdir:
    description: Store temporary files in this directory.
    type: str
  state:
    description:
      - Only C(present) is supported. Vzdump defaults cannot be removed.
    type: str
    choices: ['present']
    default: present
author:
  - sfulmer
'''

EXAMPLES = r'''
- name: Set cluster-wide vzdump defaults
  stevefulme1.proxmox.proxmox_vzdump_defaults:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    compress: zstd
    mode: snapshot
    mailto: admin@example.com
    maxfiles: 3

- name: Set node-level vzdump defaults
  stevefulme1.proxmox.proxmox_vzdump_defaults:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    compress: lzo
    dumpdir: /mnt/backups
    bwlimit: 10240
'''

RETURN = r'''
defaults:
  description: The vzdump default settings after the operation.
  returned: success
  type: dict
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule

CONFIGURABLE_PARAMS = [
    'bwlimit', 'compress', 'dumpdir', 'ionice', 'lockwait',
    'mailnotification', 'mailto', 'maxfiles', 'mode', 'pigz', 'tmpdir',
]


def main():
    argument_spec = dict(
        node=dict(type='str'),
        bwlimit=dict(type='int'),
        compress=dict(type='str', choices=['0', 'gzip', 'lzo', 'zstd']),
        dumpdir=dict(type='str'),
        ionice=dict(type='int'),
        lockwait=dict(type='int'),
        mailnotification=dict(type='str', choices=['always', 'failure']),
        mailto=dict(type='str'),
        maxfiles=dict(type='int'),
        mode=dict(type='str', choices=['snapshot', 'suspend', 'stop']),
        pigz=dict(type='int'),
        tmpdir=dict(type='str'),
        state=dict(type='str', default='present', choices=['present']),
    )

    proxmox = ProxmoxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module = proxmox.module
    params = module.params
    node = params.get('node')

    api = proxmox.get_api()

    # Build desired parameters
    desired = {}
    for param in CONFIGURABLE_PARAMS:
        value = params.get(param)
        if value is not None:
            desired[param] = value

    if not desired:
        module.exit_json(changed=False, defaults={})

    # Get current defaults
    try:
        if node:
            current = api.nodes(node).vzdump.defaults.get()
        else:
            current = api.cluster.options.get()
    except Exception as e:
        module.fail_json(msg="Failed to get vzdump defaults: %s" % str(e))

    # Determine if changes are needed
    changed = False
    update_params = {}
    for key, value in desired.items():
        current_val = current.get(key)
        if current_val is None or str(current_val) != str(value):
            update_params[key] = value

    if update_params:
        changed = True
        if not module.check_mode:
            try:
                if node:
                    api.nodes(node).vzdump.defaults.put(**update_params)
                else:
                    api.cluster.options.put(**update_params)
            except Exception as e:
                module.fail_json(msg="Failed to update vzdump defaults: %s" % str(e))

    # Re-read current state
    result_defaults = dict(current)
    result_defaults.update(desired)

    module.exit_json(changed=changed, defaults=result_defaults)


if __name__ == '__main__':
    main()
