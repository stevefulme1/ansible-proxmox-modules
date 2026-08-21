# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module_utils: _resource_paths
short_description: Proxmox API resource path mapping and resolution utilities
description:
  - Maps user-friendly resource type names (vm, lxc, container, storage, pool,
    sdn_zone, sdn_vnet) to their corresponding Proxmox API paths and identifier
    fields via the RESOURCE_TYPE_MAP dictionary.
  - Provides helpers for building and parsing Proxmox API resource paths, and
    for resolving VMs and containers by name or VMID using the cluster resources
    API.
author:
  - Steve Fulmer (@stevefulme1)
"""


# Map user-friendly resource type names to Proxmox API paths and identifier fields.
RESOURCE_TYPE_MAP = {
    'vm': {
        'api_type': 'qemu',
        'id_field': 'vmid',
        'name_field': 'name',
        'description': 'QEMU virtual machine',
    },
    'qemu': {
        'api_type': 'qemu',
        'id_field': 'vmid',
        'name_field': 'name',
        'description': 'QEMU virtual machine',
    },
    'lxc': {
        'api_type': 'lxc',
        'id_field': 'vmid',
        'name_field': 'name',
        'description': 'LXC container',
    },
    'container': {
        'api_type': 'lxc',
        'id_field': 'vmid',
        'name_field': 'name',
        'description': 'LXC container',
    },
    'node': {
        'api_type': 'node',
        'id_field': 'node',
        'name_field': 'node',
        'description': 'Cluster node',
    },
    'storage': {
        'api_type': 'storage',
        'id_field': 'storage',
        'name_field': 'storage',
        'description': 'Storage resource',
    },
    'pool': {
        'api_type': 'pool',
        'id_field': 'poolid',
        'name_field': 'poolid',
        'description': 'Resource pool',
    },
    'sdn_zone': {
        'api_type': 'sdn/zones',
        'id_field': 'zone',
        'name_field': 'zone',
        'description': 'SDN zone',
    },
    'sdn_vnet': {
        'api_type': 'sdn/vnets',
        'id_field': 'vnet',
        'name_field': 'vnet',
        'description': 'SDN virtual network',
    },
}


SUPPORTED_TYPES = sorted(RESOURCE_TYPE_MAP.keys())


def validate_resource_type(resource_type):
    """Validate and return the resource type mapping, or raise ValueError."""
    if resource_type not in RESOURCE_TYPE_MAP:
        raise ValueError(
            "Unsupported resource type '%s'. Supported types: %s"
            % (resource_type, ', '.join(SUPPORTED_TYPES))
        )
    return RESOURCE_TYPE_MAP[resource_type]


def normalize_path(path):
    """Normalize a Proxmox resource path by stripping leading/trailing slashes."""
    return path.strip('/')


def build_resource_path(node=None, resource_type=None, resource_id=None):
    """
    Build a Proxmox API resource path from components.

    Examples:
        build_resource_path('pve1', 'qemu', 100) -> 'nodes/pve1/qemu/100'
        build_resource_path('pve1') -> 'nodes/pve1'
        build_resource_path() -> ''
    """
    parts = []
    if node:
        parts.extend(['nodes', str(node)])
    if resource_type:
        parts.append(str(resource_type))
    if resource_id is not None:
        parts.append(str(resource_id))
    return '/'.join(parts)


def parse_resource_path(path):
    """
    Parse a Proxmox resource path into components.

    Examples:
        'nodes/pve1/qemu/100' -> {'node': 'pve1', 'type': 'qemu', 'id': '100'}
        'nodes/pve1' -> {'node': 'pve1', 'type': None, 'id': None}
        'storage/local' -> {'node': None, 'type': 'storage', 'id': 'local'}

    Returns:
        dict with keys: node, type, id
    """
    path = normalize_path(path)
    parts = path.split('/')
    result = {'node': None, 'type': None, 'id': None}

    if not parts or parts == ['']:
        return result

    if parts[0] == 'nodes' and len(parts) >= 2:
        result['node'] = parts[1]
        if len(parts) >= 3:
            result['type'] = parts[2]
        if len(parts) >= 4:
            result['id'] = parts[3]
    elif parts[0] == 'cluster' and len(parts) >= 2:
        result['type'] = '/'.join(parts[:2])
        if len(parts) >= 3:
            result['id'] = parts[2]
    else:
        result['type'] = parts[0]
        if len(parts) >= 2:
            result['id'] = parts[1]

    return result


def find_resource_by_name(resources, name_field, name):
    """
    Find a resource in a list of resource dicts by its name field.

    Returns:
        list of matching resource dicts
    """
    return [r for r in resources if r.get(name_field) == name]


def find_resource_by_id(resources, id_field, resource_id):
    """
    Find a resource in a list of resource dicts by its ID field.

    Returns:
        The matching resource dict, or None
    """
    for r in resources:
        if str(r.get(id_field, '')) == str(resource_id):
            return r
    return None


def get_vmid_from_name(api, name, node=None, vm_type=None):
    """
    Resolve a VM/container name to its VMID using the cluster resources API.

    Args:
        api: ProxmoxAPI instance
        name: VM or container name to search for
        node: Optional node filter
        vm_type: Optional type filter ('qemu' or 'lxc')

    Returns:
        list of dicts with vmid, name, node, type, status for each match
    """
    resources = api.cluster.resources.get(type='vm')
    matches = []
    for r in resources:
        if r.get('name') != name:
            continue
        if node and r.get('node') != node:
            continue
        if vm_type and r.get('type') != vm_type:
            continue
        matches.append({
            'vmid': r.get('vmid'),
            'name': r.get('name'),
            'node': r.get('node'),
            'type': r.get('type'),
            'status': r.get('status'),
        })
    return matches


def get_node_for_vmid(api, vmid):
    """
    Find which node a VM/container is running on by VMID.

    Args:
        api: ProxmoxAPI instance
        vmid: The VMID to locate

    Returns:
        dict with node, type, name, status or None if not found
    """
    resources = api.cluster.resources.get(type='vm')
    for r in resources:
        if str(r.get('vmid', '')) == str(vmid):
            return {
                'node': r.get('node'),
                'type': r.get('type'),
                'name': r.get('name'),
                'status': r.get('status'),
            }
    return None


def list_resources_by_type(api, resource_type, node=None):
    """
    List all resources of a given type from the cluster resources API.

    Args:
        api: ProxmoxAPI instance
        resource_type: One of 'vm', 'storage', 'node'
        node: Optional node name to filter results

    Returns:
        list of resource dicts
    """
    type_filter = resource_type
    if resource_type in ('qemu', 'lxc'):
        type_filter = 'vm'

    resources = api.cluster.resources.get(type=type_filter)

    if resource_type in ('qemu', 'lxc'):
        resources = [r for r in resources if r.get('type') == resource_type]

    if node:
        resources = [r for r in resources if r.get('node') == node]

    return resources
