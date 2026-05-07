# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
name: resource_id
author: sfulmer
version_added: "1.0.0"
short_description: Look up Proxmox resource IDs by name or path
description:
  - This lookup plugin resolves Proxmox VE resource names or inventory paths
    to their resource identifiers (VMIDs, node names, storage IDs, etc.).
  - It queries the Proxmox cluster resources API and returns matching IDs,
    enabling indirect referencing of resources in playbooks.
  - Supports VMs, containers, nodes, storage, pools, SDN zones, and SDN VNets.
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
  - stevefulme1.proxmox.lookup_base_options
options:
  _terms:
    description:
      - A list of resource names or paths to resolve.
      - Names are matched against the name field for the given resource type.
      - Paths use the format C(nodes/<node>/<type>/<id>) and are validated directly.
    required: true
    type: list
    elements: str
  resource_type:
    description:
      - The type of Proxmox resource to search for.
      - Required when looking up by name. Ignored when looking up by path.
    type: str
    choices:
      - vm
      - qemu
      - lxc
      - container
      - node
      - storage
      - pool
      - sdn_zone
      - sdn_vnet
  node:
    description:
      - Restrict the search to a specific cluster node.
      - Only applies to VM, container, and storage lookups.
    type: str
'''

EXAMPLES = r'''
# Look up a VM's VMID by name
- name: Get VMID for webserver
  ansible.builtin.debug:
    msg: "{{ lookup('stevefulme1.proxmox.resource_id', 'webserver', resource_type='vm') }}"

# Look up multiple VMs
- name: Get VMIDs for several VMs
  ansible.builtin.debug:
    msg: "{{ lookup('stevefulme1.proxmox.resource_id', 'web1', 'web2', 'db1', resource_type='vm', wantlist=True) }}"

# Look up VM on a specific node
- name: Get VMID on pve1
  ansible.builtin.debug:
    msg: "{{ lookup('stevefulme1.proxmox.resource_id', 'webserver', resource_type='vm', node='pve1') }}"

# Look up a container by name
- name: Get container VMID
  ansible.builtin.debug:
    msg: "{{ lookup('stevefulme1.proxmox.resource_id', 'dns-server', resource_type='lxc') }}"

# Look up storage ID
- name: Get storage resource
  ansible.builtin.debug:
    msg: "{{ lookup('stevefulme1.proxmox.resource_id', 'ceph-pool', resource_type='storage') }}"

# Look up by path (no resource_type needed)
- name: Get VM by path
  ansible.builtin.debug:
    msg: "{{ lookup('stevefulme1.proxmox.resource_id', 'nodes/pve1/qemu/100') }}"

# Use in a task to reference a VM indirectly
- name: Snapshot a VM found by name
  stevefulme1.proxmox.proxmox_vm_snapshot:
    api_host: "{{ proxmox_host }}"
    api_user: "{{ proxmox_user }}"
    api_password: "{{ proxmox_password }}"
    node: pve1
    vmid: "{{ lookup('stevefulme1.proxmox.resource_id', 'webserver', resource_type='vm') }}"
    snapname: pre-upgrade
    state: present

# Use with environment variables for auth (PROXMOX_HOST, PROXMOX_USER, etc.)
- name: Look up with env-based auth
  ansible.builtin.debug:
    msg: "{{ lookup('stevefulme1.proxmox.resource_id', 'myvm', resource_type='vm') }}"
'''

RETURN = r'''
_raw:
  description:
    - A list of resource identifiers matching the query terms.
    - For VMs and containers, returns VMIDs as strings.
    - For nodes, returns node names.
    - For storage, returns storage IDs.
    - For pools, returns pool IDs.
    - For SDN zones/vnets, returns zone/vnet names.
  type: list
  elements: str
'''

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False

from ansible_collections.stevefulme1.proxmox.plugins.module_utils._resource_paths import (
    validate_resource_type,
    parse_resource_path,
    find_resource_by_name,
    SUPPORTED_TYPES,
)

display = Display()


class LookupModule(LookupBase):

    def _get_api(self, variables, **kwargs):
        """Create and return a ProxmoxAPI connection from lookup options."""
        api_host = self.get_option('api_host')
        api_user = self.get_option('api_user')
        api_password = self.get_option('api_password')
        api_token_id = self.get_option('api_token_id')
        api_token_secret = self.get_option('api_token_secret')
        validate_certs = self.get_option('validate_certs')

        if not api_host:
            raise AnsibleError("api_host is required. Set it as an option or via PROXMOX_HOST environment variable.")
        if not api_user:
            raise AnsibleError("api_user is required. Set it as an option or via PROXMOX_USER environment variable.")

        auth_args = dict(
            host=api_host,
            user=api_user,
            verify_ssl=validate_certs,
        )

        if api_token_id and api_token_secret:
            auth_args['token_name'] = api_token_id
            auth_args['token_value'] = api_token_secret
        elif api_password:
            auth_args['password'] = api_password
        else:
            raise AnsibleError(
                "Either api_password or api_token_id+api_token_secret is required. "
                "Set via options or PROXMOX_PASSWORD / PROXMOX_TOKEN_ID + PROXMOX_TOKEN_SECRET environment variables."
            )

        try:
            return ProxmoxAPI(**auth_args)
        except Exception as e:
            raise AnsibleError("Failed to connect to Proxmox API at '%s': %s" % (api_host, str(e)))

    def _resolve_by_path(self, api, path, fail_on_missing):
        """Resolve a resource by its API path. Returns the resource ID or empty string."""
        parsed = parse_resource_path(path)
        if parsed['id'] is not None:
            return str(parsed['id'])

        if parsed['node'] and not parsed['type']:
            # Path is just "nodes/<name>" — validate node exists
            try:
                nodes = api.nodes.get()
                for n in nodes:
                    if n.get('node') == parsed['node']:
                        return parsed['node']
            except Exception as e:
                raise AnsibleError("Failed to query nodes: %s" % str(e))

            if fail_on_missing:
                raise AnsibleError("Node '%s' not found" % parsed['node'])
            return ''

        if fail_on_missing:
            raise AnsibleError("Cannot resolve path '%s' — no resource ID found" % path)
        return ''

    def _resolve_by_name(self, api, name, resource_type, node, fail_on_missing):
        """Resolve a resource name to its ID using the cluster resources API."""
        type_info = validate_resource_type(resource_type)
        api_type = type_info['api_type']
        id_field = type_info['id_field']
        name_field = type_info['name_field']

        try:
            if api_type in ('qemu', 'lxc'):
                resources = api.cluster.resources.get(type='vm')
                if api_type in ('qemu', 'lxc'):
                    resources = [r for r in resources if r.get('type') == api_type]
            elif api_type == 'node':
                resources = api.nodes.get()
            elif api_type == 'storage':
                resources = api.storage.get()
            elif api_type == 'pool':
                resources = api.pools.get()
            elif api_type == 'sdn/zones':
                resources = api.cluster.sdn.zones.get()
            elif api_type == 'sdn/vnets':
                resources = api.cluster.sdn.vnets.get()
            else:
                resources = api.cluster.resources.get()
        except Exception as e:
            raise AnsibleError("Failed to query Proxmox resources (type=%s): %s" % (api_type, str(e)))

        if node:
            resources = [r for r in resources if r.get('node') == node]

        matches = find_resource_by_name(resources, name_field, name)

        if not matches:
            if fail_on_missing:
                node_msg = " on node '%s'" % node if node else ""
                raise AnsibleError(
                    "Resource '%s' of type '%s'%s not found" % (name, resource_type, node_msg)
                )
            return ''

        if len(matches) > 1:
            display.warning(
                "Multiple resources named '%s' found (type=%s). Returning first match. "
                "Use 'node' option to narrow results." % (name, resource_type)
            )

        return str(matches[0].get(id_field, ''))

    def run(self, terms, variables=None, **kwargs):
        if not HAS_PROXMOXER:
            raise AnsibleError("The proxmoxer library is required. Install it with: pip install proxmoxer")

        self.set_options(var_options=variables, direct=kwargs)

        fail_on_missing = self.get_option('fail_on_missing')
        resource_type = kwargs.get('resource_type')
        node = kwargs.get('node')

        api = self._get_api(variables, **kwargs)
        results = []

        for term in terms:
            term = str(term).strip()

            # Determine if this is a path or a name lookup
            if '/' in term:
                display.vvv("Proxmox lookup: resolving path '%s'" % term)
                result = self._resolve_by_path(api, term, fail_on_missing)
            else:
                if not resource_type:
                    raise AnsibleError(
                        "resource_type is required when looking up by name. "
                        "Supported types: %s" % ', '.join(SUPPORTED_TYPES)
                    )
                display.vvv("Proxmox lookup: resolving name '%s' (type=%s, node=%s)" % (term, resource_type, node))
                result = self._resolve_by_name(api, term, resource_type, node, fail_on_missing)

            if result:
                results.append(result)

        return results
