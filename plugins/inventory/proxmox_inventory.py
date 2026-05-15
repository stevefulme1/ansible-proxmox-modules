#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
name: proxmox_inventory
plugin_type: inventory
short_description: Dynamic inventory plugin for Proxmox VE
description:
  - Discovers QEMU/KVM VMs and LXC containers across all Proxmox VE nodes.
  - Groups hosts by node name, VM type (qemu/lxc), running state, and tags.
  - Populates host variables including vmid, node, status, memory, cores, and IP addresses.
  - IP addresses are retrieved from the QEMU guest agent when available.
version_added: "1.0.0"
author:
  - sfulmer
options:
  plugin:
    description:
      - Token that ensures this is a source file for the plugin.
    type: str
    required: true
    choices:
      - stevefulme1.proxmox.proxmox_inventory
  api_host:
    description:
      - The Proxmox VE API host (hostname or IP).
    type: str
    required: true
    env:
      - name: PROXMOX_HOST
  api_user:
    description:
      - The Proxmox VE API user (e.g. C(root@pam)).
    type: str
    required: true
    env:
      - name: PROXMOX_USER
  api_password:
    description:
      - The password for API authentication.
    type: str
    env:
      - name: PROXMOX_PASSWORD
  api_token_id:
    description:
      - The API token ID for token-based authentication.
    type: str
    env:
      - name: PROXMOX_TOKEN_ID
  api_token_secret:
    description:
      - The API token secret for token-based authentication.
    type: str
    env:
      - name: PROXMOX_TOKEN_SECRET
  validate_certs:
    description:
      - Whether to validate SSL certificates.
    type: bool
    default: true
    env:
      - name: PROXMOX_VALIDATE_CERTS
  want_agents:
    description:
      - Whether to query the QEMU guest agent for IP addresses.
      - Requires the guest agent to be running inside the VM.
    type: bool
    default: true
'''

EXAMPLES = r'''
# proxmox.yml - minimal inventory source
plugin: stevefulme1.proxmox.proxmox_inventory
api_host: proxmox.example.com
api_user: root@pam
api_token_id: mytoken
api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# proxmox.yml - with environment variables and no agent queries
plugin: stevefulme1.proxmox.proxmox_inventory
api_host: proxmox.example.com
api_user: root@pam
api_password: secret
validate_certs: false
want_agents: false
'''

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False

from ansible.errors import AnsibleError
from ansible.plugins.inventory import BaseInventoryPlugin


class InventoryModule(BaseInventoryPlugin):
    """Dynamic inventory plugin for Proxmox VE."""

    NAME = 'stevefulme1.proxmox.proxmox_inventory'

    def verify_file(self, path):
        """Verify that the source file can be used by this plugin."""
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('.proxmox.yml', '.proxmox.yaml', 'proxmox.yml', 'proxmox.yaml')):
                valid = True
        return valid

    def _get_api(self):
        """Create and return a ProxmoxAPI connection."""
        auth_args = dict(
            host=self.get_option('api_host'),
            user=self.get_option('api_user'),
            verify_ssl=self.get_option('validate_certs'),
        )

        token_id = self.get_option('api_token_id')
        token_secret = self.get_option('api_token_secret')
        password = self.get_option('api_password')

        if token_id and token_secret:
            auth_args['token_name'] = token_id
            auth_args['token_value'] = token_secret
        elif password:
            auth_args['password'] = password
        else:
            raise AnsibleError('Either api_password or both api_token_id and api_token_secret are required.')

        try:
            return ProxmoxAPI(**auth_args)
        except Exception as e:
            raise AnsibleError('Failed to connect to Proxmox API: %s' % str(e))

    def _get_agent_ip(self, api, node, vmid):
        """Try to get IP addresses from the QEMU guest agent."""
        ips = []
        try:
            interfaces = api.nodes(node).qemu(vmid).agent('network-get-interfaces').get()
            for iface in interfaces.get('result', []):
                if iface.get('name') == 'lo':
                    continue
                for addr in iface.get('ip-addresses', []):
                    if addr.get('ip-address-type') == 'ipv4':
                        ips.append(addr.get('ip-address'))
        except Exception:
            pass
        return ips

    def _sanitize_group(self, name):
        """Sanitize a string for use as an Ansible group name."""
        return name.replace('-', '_').replace('.', '_').replace(' ', '_')

    def _add_guest(self, api, node_name, guest, guest_type):
        """Add a single VM or container to the inventory."""
        vmid = guest.get('vmid')
        name = guest.get('name', '') or guest.get('hostname', '')
        status = guest.get('status', 'unknown')

        # Use name if available, otherwise use type-vmid
        if name:
            hostname = name
        else:
            hostname = '%s-%s' % (guest_type, vmid)

        self.inventory.add_host(hostname)

        # Set host variables
        self.inventory.set_variable(hostname, 'proxmox_vmid', vmid)
        self.inventory.set_variable(hostname, 'proxmox_node', node_name)
        self.inventory.set_variable(hostname, 'proxmox_type', guest_type)
        self.inventory.set_variable(hostname, 'proxmox_status', status)
        self.inventory.set_variable(hostname, 'proxmox_name', name)

        if guest.get('maxmem'):
            self.inventory.set_variable(hostname, 'proxmox_memory', int(guest['maxmem']) // (1024 * 1024))
        if guest.get('cpus'):
            self.inventory.set_variable(hostname, 'proxmox_cores', guest['cpus'])

        # Group by node
        node_group = self._sanitize_group('node_%s' % node_name)
        self.inventory.add_group(node_group)
        self.inventory.add_child(node_group, hostname)

        # Group by type (qemu / lxc)
        type_group = self._sanitize_group(guest_type)
        self.inventory.add_group(type_group)
        self.inventory.add_child(type_group, hostname)

        # Group by status (running / stopped / etc.)
        status_group = self._sanitize_group('status_%s' % status)
        self.inventory.add_group(status_group)
        self.inventory.add_child(status_group, hostname)

        # Group by tags
        tags_raw = guest.get('tags', '')
        if tags_raw:
            for tag in tags_raw.split(';'):
                tag = tag.strip()
                if tag:
                    tag_group = self._sanitize_group('tag_%s' % tag)
                    self.inventory.add_group(tag_group)
                    self.inventory.add_child(tag_group, hostname)

        # Retrieve IP addresses from guest agent for QEMU VMs
        if guest_type == 'qemu' and status == 'running' and self.get_option('want_agents'):
            ips = self._get_agent_ip(api, node_name, vmid)
            if ips:
                self.inventory.set_variable(hostname, 'proxmox_ip_addresses', ips)
                self.inventory.set_variable(hostname, 'ansible_host', ips[0])

    def parse(self, inventory, loader, path, cache=True):
        """Parse the inventory source and populate the inventory."""
        super(InventoryModule, self).parse(inventory, loader, path, cache)

        if not HAS_PROXMOXER:
            raise AnsibleError('The proxmoxer library is required. Install it with: pip install proxmoxer')

        self._read_config_data(path)

        api = self._get_api()

        # Get all nodes
        try:
            nodes = api.nodes.get()
        except Exception as e:
            raise AnsibleError('Failed to get Proxmox nodes: %s' % str(e))

        for node in nodes:
            node_name = node['node']

            # Get QEMU VMs on this node
            try:
                vms = api.nodes(node_name).qemu.get()
                for vm in vms:
                    self._add_guest(api, node_name, vm, 'qemu')
            except Exception as e:
                self.display.warning('Failed to get VMs from node %s: %s' % (node_name, str(e)))

            # Get LXC containers on this node
            try:
                containers = api.nodes(node_name).lxc.get()
                for ct in containers:
                    self._add_guest(api, node_name, ct, 'lxc')
            except Exception as e:
                self.display.warning('Failed to get containers from node %s: %s' % (node_name, str(e)))
