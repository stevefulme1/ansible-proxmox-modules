# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

"""Tests for proxmox_node_network module.

Note: this module uses raw AnsibleModule + ProxmoxAPI directly (not ProxmoxModule).
"""

import pytest
from unittest.mock import MagicMock, patch

from tests.unit.conftest import set_module_args

# proxmox_node_network imports ProxmoxAPI directly from proxmoxer
PROXMOXER_PATH = "ansible_collections.stevefulme1.proxmox.plugins.modules.proxmox_node_network.ProxmoxAPI"


def _run_module():
    from ansible_collections.stevefulme1.proxmox.plugins.modules import (
        proxmox_node_network,
    )

    with pytest.raises(SystemExit) as exc_info:
        proxmox_node_network.main()
    return exc_info.value.code


class TestNodeNetworkCreateBridge:
    """Creating a bridge interface."""

    @patch(PROXMOXER_PATH)
    def test_create_bridge(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        # No existing interface
        api.nodes.return_value.network.return_value.get.side_effect = Exception("not found")

        module_args.update(
            node="pve1",
            iface="vmbr0",
            type="bridge",
            address="192.168.1.1",
            netmask="255.255.255.0",
            gateway="192.168.1.254",
            bridge_ports="eno1",
            bridge_vlan_aware=True,
            autostart=True,
            state="present",
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.nodes.return_value.network.post.assert_called_once()
        call_kwargs = api.nodes.return_value.network.post.call_args[1]
        assert call_kwargs["iface"] == "vmbr0"
        assert call_kwargs["type"] == "bridge"


class TestNodeNetworkCreateBond:
    """Creating a bond interface."""

    @patch(PROXMOXER_PATH)
    def test_create_bond(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.nodes.return_value.network.return_value.get.side_effect = Exception("not found")

        module_args.update(
            node="pve1",
            iface="bond0",
            type="bond",
            bond_mode="802.3ad",
            slaves="eno1 eno2",
            autostart=True,
            state="present",
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        call_kwargs = api.nodes.return_value.network.post.call_args[1]
        assert call_kwargs["iface"] == "bond0"
        assert call_kwargs["bond_mode"] == "802.3ad"


class TestNodeNetworkDelete:
    """Removing a network interface."""

    @patch(PROXMOXER_PATH)
    def test_delete_interface(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.nodes.return_value.network.return_value.get.return_value = {
            "iface": "vmbr1",
            "type": "bridge",
        }

        module_args.update(node="pve1", iface="vmbr1", state="absent")
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.nodes.return_value.network.return_value.delete.assert_called_once()


class TestNodeNetworkIdempotent:
    """Interface already matches desired config."""

    @patch(PROXMOXER_PATH)
    def test_no_change_when_matching(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.nodes.return_value.network.return_value.get.return_value = {
            "iface": "vmbr0",
            "type": "bridge",
            "address": "192.168.1.1",
            "netmask": "255.255.255.0",
            "autostart": 1,
        }

        module_args.update(
            node="pve1",
            iface="vmbr0",
            type="bridge",
            address="192.168.1.1",
            netmask="255.255.255.0",
            autostart=True,
            state="present",
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.nodes.return_value.network.return_value.put.assert_not_called()
