# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

"""Tests for proxmox_sdn_zone module."""

import pytest
from unittest.mock import MagicMock, patch

from tests.unit.conftest import set_module_args

MODULE_PATH = (
    "ansible_collections.stevefulme1.proxmox.plugins.modules.proxmox_sdn_zone"
)
MODULE_UTILS_PATH = (
    "ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox"
)


def _run_module():
    from ansible_collections.stevefulme1.proxmox.plugins.modules import (
        proxmox_sdn_zone,
    )

    with pytest.raises(SystemExit) as exc_info:
        proxmox_sdn_zone.main()
    return exc_info.value.code


class TestSdnZoneCreate:
    """Creating new SDN zones."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_create_simple_zone(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.cluster.sdn.zones.get.return_value = []

        module_args.update(zone="testzone", type="simple", state="present")
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.cluster.sdn.zones.post.assert_called_once()
        call_kwargs = api.cluster.sdn.zones.post.call_args[1]
        assert call_kwargs["zone"] == "testzone"
        assert call_kwargs["type"] == "simple"

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_create_vlan_zone(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.cluster.sdn.zones.get.return_value = []

        module_args.update(
            zone="vlanzone",
            type="vlan",
            bridge="vmbr0",
            tag=100,
            state="present",
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        call_kwargs = api.cluster.sdn.zones.post.call_args[1]
        assert call_kwargs["type"] == "vlan"
        assert call_kwargs["bridge"] == "vmbr0"
        assert call_kwargs["tag"] == 100

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_create_vxlan_zone(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.cluster.sdn.zones.get.return_value = []

        module_args.update(zone="vxzone", type="vxlan", state="present")
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        call_kwargs = api.cluster.sdn.zones.post.call_args[1]
        assert call_kwargs["type"] == "vxlan"


class TestSdnZoneDelete:
    """Removing an existing SDN zone."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_delete_zone(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.cluster.sdn.zones.get.return_value = [
            {"zone": "oldzone", "type": "simple"},
        ]

        module_args.update(zone="oldzone", state="absent")
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.cluster.sdn.zones.return_value.delete.assert_called_once()


class TestSdnZoneIdempotent:
    """Zone already matches desired state."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_existing_zone_no_change(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.cluster.sdn.zones.get.return_value = [
            {"zone": "testzone", "type": "simple"},
        ]

        module_args.update(zone="testzone", type="simple", state="present")
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.cluster.sdn.zones.post.assert_not_called()


class TestSdnZoneUpdate:
    """Zone exists but needs parameter changes."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_update_zone_mtu(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.cluster.sdn.zones.get.return_value = [
            {"zone": "testzone", "type": "simple", "mtu": 1500},
        ]

        module_args.update(zone="testzone", type="simple", mtu=9000, state="present")
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.cluster.sdn.zones.return_value.put.assert_called_once()
