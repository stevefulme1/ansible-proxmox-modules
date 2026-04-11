# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_network
short_description: Manage network interfaces on Proxmox VE nodes
version_added: "0.1.0"
description:
  - Create, update, or remove network interface configurations on Proxmox VE nodes
    via the C(/nodes/{node}/network) API endpoint.
  - After making changes, the network configuration must be applied (reloaded) on the
    node for changes to take effect. This module modifies the pending configuration only.
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
  iface:
    description: The network interface name (e.g. C(vmbr0), C(bond0), C(eth0)).
    type: str
    required: true
  type:
    description: The interface type.
    type: str
    choices: ['bridge', 'bond', 'vlan', 'eth', 'OVSBridge', 'OVSBond', 'OVSPort', 'OVSIntPort']
  address:
    description: IPv4 address.
    type: str
  netmask:
    description: IPv4 netmask.
    type: str
  gateway:
    description: IPv4 default gateway.
    type: str
  address6:
    description: IPv6 address.
    type: str
  netmask6:
    description: IPv6 netmask (prefix length).
    type: str
  gateway6:
    description: IPv6 default gateway.
    type: str
  bridge_ports:
    description: Space-separated list of bridge ports (for bridge interfaces).
    type: str
  bridge_vlan_aware:
    description: Enable VLAN-aware bridge mode.
    type: bool
  bond_mode:
    description: Bonding mode.
    type: str
    choices:
      - balance-rr
      - active-backup
      - balance-xor
      - broadcast
      - 802.3ad
      - balance-tlb
      - balance-alb
  bond_primary:
    description: Primary interface for active-backup bond mode.
    type: str
  slaves:
    description: Space-separated list of bond slave interfaces.
    type: str
  vlan_raw_device:
    description: The underlying physical device for a VLAN interface.
    type: str
  vlan_id:
    description: VLAN tag number.
    type: int
  mtu:
    description: Maximum transmission unit size.
    type: int
  cidr:
    description: IPv4 CIDR notation (e.g. C(192.168.1.1/24)). Alternative to address/netmask.
    type: str
  autostart:
    description: Whether to bring the interface up on boot.
    type: bool
    default: true
  comments:
    description: Comments/description for the interface.
    type: str
  state:
    description: Whether the interface should be present or absent.
    type: str
    choices: ['present', 'absent']
    default: present
notes:
  - After creating or modifying network interfaces, you must apply the pending
    network configuration on the node for changes to take effect. This can be done
    via the Proxmox web UI or by calling the API endpoint
    C(PUT /nodes/{node}/network) with no parameters (reload).
  - Deleting the last bridge interface may make the node unreachable.
author:
  - "Proxmox Community (@proxmox-community)"
'''

EXAMPLES = r'''
- name: Create a VLAN-aware bridge
  proxmox_node_network:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    iface: vmbr0
    type: bridge
    address: 192.168.1.1
    netmask: 255.255.255.0
    gateway: 192.168.1.254
    bridge_ports: "eno1"
    bridge_vlan_aware: true
    autostart: true
    state: present

- name: Create a bond interface
  proxmox_node_network:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    iface: bond0
    type: bond
    bond_mode: 802.3ad
    slaves: "eno1 eno2"
    autostart: true
    state: present

- name: Remove a network interface
  proxmox_node_network:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    iface: vmbr1
    state: absent
'''

RETURN = r'''
iface:
  description: The network interface name that was managed.
  returned: success
  type: str
  sample: "vmbr0"
node:
  description: The node on which the interface was managed.
  returned: success
  type: str
  sample: "pve1"
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


# Map module parameter names to API parameter names where they differ
PARAM_MAP = dict(
    address6='address6',
    netmask6='netmask6',
    gateway6='gateway6',
    bridge_ports='bridge_ports',
    bridge_vlan_aware='bridge_vlan_aware',
    bond_mode='bond_mode',
    bond_primary='bond-primary',
    slaves='slaves',
    vlan_raw_device='vlan-raw-device',
    vlan_id='vlan-id',
)

# Parameters that are sent to the API
CONFIGURABLE_PARAMS = [
    'type', 'address', 'netmask', 'gateway', 'address6', 'netmask6', 'gateway6',
    'bridge_ports', 'bridge_vlan_aware', 'bond_mode', 'bond_primary', 'slaves',
    'vlan_raw_device', 'vlan_id', 'mtu', 'cidr', 'autostart', 'comments',
]


def get_iface(proxmox, node, iface):
    """Return interface config dict or None if not found."""
    try:
        return proxmox.nodes(node).network(iface).get()
    except Exception:
        return None


def build_api_params(params):
    """Build API parameter dict from module params, converting names as needed."""
    api_params = {}
    for param in CONFIGURABLE_PARAMS:
        value = params.get(param)
        if value is None:
            continue
        # Convert parameter name if needed
        api_key = PARAM_MAP.get(param, param)
        # Convert booleans to integers for the API
        if isinstance(value, bool):
            value = 1 if value else 0
        api_params[api_key] = value
    return api_params


def main():
    argument_spec = dict(
        api_host=dict(type='str', required=True),
        api_user=dict(type='str', required=True),
        api_password=dict(type='str', no_log=True),
        api_token_id=dict(type='str'),
        api_token_secret=dict(type='str', no_log=True),
        validate_certs=dict(type='bool', default=True),
        node=dict(type='str', required=True),
        iface=dict(type='str', required=True),
        type=dict(
            type='str',
            choices=['bridge', 'bond', 'vlan', 'eth', 'OVSBridge', 'OVSBond', 'OVSPort', 'OVSIntPort'],
        ),
        address=dict(type='str'),
        netmask=dict(type='str'),
        gateway=dict(type='str'),
        address6=dict(type='str'),
        netmask6=dict(type='str'),
        gateway6=dict(type='str'),
        bridge_ports=dict(type='str'),
        bridge_vlan_aware=dict(type='bool'),
        bond_mode=dict(
            type='str',
            choices=['balance-rr', 'active-backup', 'balance-xor', 'broadcast',
                     '802.3ad', 'balance-tlb', 'balance-alb'],
        ),
        bond_primary=dict(type='str'),
        slaves=dict(type='str'),
        vlan_raw_device=dict(type='str'),
        vlan_id=dict(type='int'),
        mtu=dict(type='int'),
        cidr=dict(type='str'),
        autostart=dict(type='bool', default=True),
        comments=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['api_password', 'api_token_id']],
        required_together=[['api_token_id', 'api_token_secret']],
        required_if=[
            ['state', 'present', ['type']],
        ],
    )

    if not HAS_PROXMOXER:
        module.fail_json(msg="proxmoxer library is required. Install it with: pip install proxmoxer")

    params = module.params
    state = params['state']
    node = params['node']
    iface = params['iface']

    auth_args = dict(
        host=params['api_host'],
        user=params['api_user'],
        verify_ssl=params['validate_certs'],
    )
    if params.get('api_token_id') and params.get('api_token_secret'):
        auth_args['token_name'] = params['api_token_id']
        auth_args['token_value'] = params['api_token_secret']
    elif params.get('api_password'):
        auth_args['password'] = params['api_password']

    try:
        proxmox = ProxmoxAPI(**auth_args)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Proxmox API: %s" % str(e))

    existing = get_iface(proxmox, node, iface)
    changed = False
    result = dict(iface=iface, node=node)

    if state == 'absent':
        if existing is not None:
            changed = True
            if not module.check_mode:
                try:
                    proxmox.nodes(node).network(iface).delete()
                except Exception as e:
                    module.fail_json(
                        msg="Failed to delete interface '%s' on node '%s': %s" % (iface, node, str(e))
                    )
        module.exit_json(changed=changed, **result)

    # state == present
    desired = build_api_params(params)

    if existing is None:
        changed = True
        if not module.check_mode:
            create_params = dict(iface=iface)
            create_params.update(desired)
            try:
                proxmox.nodes(node).network.post(**create_params)
            except Exception as e:
                module.fail_json(
                    msg="Failed to create interface '%s' on node '%s': %s" % (iface, node, str(e))
                )
    else:
        update_params = {}
        for key, value in desired.items():
            current_val = existing.get(key)
            if current_val is None or str(current_val) != str(value):
                update_params[key] = value
        if update_params:
            changed = True
            if not module.check_mode:
                try:
                    proxmox.nodes(node).network(iface).put(**update_params)
                except Exception as e:
                    module.fail_json(
                        msg="Failed to update interface '%s' on node '%s': %s" % (iface, node, str(e))
                    )

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
