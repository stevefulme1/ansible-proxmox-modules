#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_ha_group
short_description: Manage Proxmox VE HA groups
description:
  - Create, update, or delete High Availability groups in a Proxmox VE cluster.
  - HA groups define which nodes a resource may run on and with what priority.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  group:
    description: The HA group name.
    type: str
    required: true
  nodes:
    description:
      - List of nodes in the HA group with optional priority.
      - Required when state is present.
    type: list
    elements: dict
    suboptions:
      node:
        description: The node name.
        type: str
        required: true
      priority:
        description: Node priority (higher values preferred).
        type: int
  comment:
    description: Comment for the HA group.
    type: str
  restricted:
    description:
      - If true, resources bound to this group can only run on nodes in this group.
    type: bool
  nofailback:
    description:
      - If true, resources will not automatically fail back to a higher-priority node.
    type: bool
  state:
    description: Whether the HA group should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create an HA group
  sfulmer.proxmox.proxmox_ha_group:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    group: ha_prod
    nodes:
      - node: pve1
        priority: 2
      - node: pve2
        priority: 1
      - node: pve3
    comment: Production HA group
    restricted: true
    nofailback: false
    state: present

- name: Remove an HA group
  sfulmer.proxmox.proxmox_ha_group:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    group: ha_prod
    state: absent
'''

RETURN = r'''
group:
  description: The HA group name that was managed.
  returned: always
  type: str
  sample: ha_prod
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def _format_nodes(nodes_list):
    """Convert list of node dicts to Proxmox HA group nodes string format.

    Format: 'node1:priority,node2:priority,node3'
    """
    parts = []
    for n in nodes_list:
        entry = n['node']
        if n.get('priority') is not None:
            entry = "%s:%d" % (entry, n['priority'])
        parts.append(entry)
    return ','.join(sorted(parts))


def main():
    node_spec = dict(
        node=dict(type='str', required=True),
        priority=dict(type='int'),
    )

    module_args = dict(
        group=dict(type='str', required=True),
        nodes=dict(type='list', elements='dict', options=node_spec),
        comment=dict(type='str'),
        restricted=dict(type='bool'),
        nofailback=dict(type='bool'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(
        argument_spec=module_args,
        required_if=[
            ('state', 'present', ['nodes']),
        ],
    )
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    group_name = params['group']
    state = params['state']

    # Get existing HA groups
    try:
        groups = api.cluster.ha.groups.get()
    except Exception as e:
        module.fail_json(msg="Failed to get HA groups: %s" % str(e))

    existing = None
    for g in groups:
        if g.get('group') == group_name:
            existing = g
            break

    changed = False
    result = dict(group=group_name, changed=False)

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.cluster.ha.groups(group_name).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete HA group '%s': %s" % (group_name, str(e)))
            changed = True
    else:
        nodes_str = _format_nodes(params['nodes'])
        config = dict(nodes=nodes_str)

        if params.get('comment') is not None:
            config['comment'] = params['comment']
        if params.get('restricted') is not None:
            config['restricted'] = int(params['restricted'])
        if params.get('nofailback') is not None:
            config['nofailback'] = int(params['nofailback'])

        if existing:
            needs_update = False
            # Compare nodes string (normalize existing for comparison)
            existing_nodes = existing.get('nodes', '')
            if isinstance(existing_nodes, str):
                existing_nodes_sorted = ','.join(sorted(existing_nodes.split(',')))
            else:
                existing_nodes_sorted = existing_nodes

            if existing_nodes_sorted != nodes_str:
                needs_update = True

            for key in ['comment', 'restricted', 'nofailback']:
                if key in config:
                    if str(existing.get(key, '')) != str(config[key]):
                        needs_update = True
                        break

            if needs_update:
                if not module.check_mode:
                    try:
                        api.cluster.ha.groups(group_name).put(**config)
                    except Exception as e:
                        module.fail_json(msg="Failed to update HA group '%s': %s" % (group_name, str(e)))
                changed = True
        else:
            config['group'] = group_name
            if not module.check_mode:
                try:
                    api.cluster.ha.groups.post(**config)
                except Exception as e:
                    module.fail_json(msg="Failed to create HA group '%s': %s" % (group_name, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
