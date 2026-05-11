# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

"""Tests for proxmox_firewall_rule module."""

import pytest
from unittest.mock import MagicMock, patch

from tests.unit.conftest import set_module_args

MODULE_PATH = (
    "ansible_collections.stevefulme1.proxmox.plugins.modules.proxmox_firewall_rule"
)
MODULE_UTILS_PATH = (
    "ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox"
)


def _run_module():
    from ansible_collections.stevefulme1.proxmox.plugins.modules import (
        proxmox_firewall_rule,
    )

    with pytest.raises(SystemExit) as exc_info:
        proxmox_firewall_rule.main()
    return exc_info.value.code


class TestFirewallRuleCreate:
    """Creating a new firewall rule."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_create_cluster_rule(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.cluster.firewall.rules.get.return_value = []

        module_args.update(
            scope="cluster",
            action="ACCEPT",
            type="in",
            proto="tcp",
            dport="22",
            comment="Allow SSH",
            state="present",
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.cluster.firewall.rules.post.assert_called_once()
        call_kwargs = api.cluster.firewall.rules.post.call_args[1]
        assert call_kwargs["action"] == "ACCEPT"
        assert call_kwargs["type"] == "in"
        assert call_kwargs["dport"] == "22"

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_create_host_rule(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.nodes.return_value = api.nodes
        api.nodes.firewall.rules.get.return_value = []

        module_args.update(
            scope="host",
            node="pve1",
            action="ACCEPT",
            type="in",
            proto="tcp",
            dport="8006",
            comment="Allow PVE UI",
            state="present",
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_create_rule_with_source_dest(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.cluster.firewall.rules.get.return_value = []

        module_args.update(
            scope="cluster",
            action="ACCEPT",
            type="in",
            proto="tcp",
            source="10.0.0.0/8",
            dest="192.168.1.1",
            dport="443",
            state="present",
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        call_kwargs = api.cluster.firewall.rules.post.call_args[1]
        assert call_kwargs["source"] == "10.0.0.0/8"
        assert call_kwargs["dest"] == "192.168.1.1"


class TestFirewallRuleDelete:
    """Removing an existing firewall rule."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_delete_by_position(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.cluster.firewall.rules.get.return_value = [
            {"pos": 0, "action": "ACCEPT", "type": "in", "proto": "tcp", "dport": "22"},
        ]

        module_args.update(scope="cluster", pos=0, state="absent")
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0


class TestFirewallRuleIdempotent:
    """Rule already exists -- no change expected."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_existing_rule_no_change(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.cluster.firewall.rules.get.return_value = [
            {
                "pos": 0,
                "action": "ACCEPT",
                "type": "in",
                "proto": "tcp",
                "dport": "22",
            },
        ]

        module_args.update(
            scope="cluster",
            action="ACCEPT",
            type="in",
            proto="tcp",
            dport="22",
            state="present",
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.cluster.firewall.rules.post.assert_not_called()
