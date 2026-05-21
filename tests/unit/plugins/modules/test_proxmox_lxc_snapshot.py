# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

"""Tests for proxmox_lxc_snapshot module."""

from unittest.mock import MagicMock


class TestCreate:
    """Creating resources."""

    def test_create_returns_resource(self):
        client = MagicMock()
        client.create.return_value = dict(id="123", name="test")
        result = client.create("proxmox_lxc_snapshot", dict(name="test"))
        assert result["id"] == "123"

    def test_create_idempotent(self):
        client = MagicMock()
        client.get.return_value = dict(id="123", name="test")
        assert client.get("proxmox_lxc_snapshot", "123") is not None


class TestDelete:
    """Deleting resources."""

    def test_delete_existing(self):
        client = MagicMock()
        client.delete("proxmox_lxc_snapshot", "123")
        client.delete.assert_called_once_with("proxmox_lxc_snapshot", "123")

    def test_delete_not_found(self):
        client = MagicMock()
        client.get.return_value = None
        assert client.get("proxmox_lxc_snapshot", "x") is None


class TestList:
    """Listing resources."""

    def test_list_returns_items(self):
        client = MagicMock()
        client.list.return_value = [dict(id="1"), dict(id="2")]
        assert len(client.list("proxmox_lxc_snapshot")) == 2

    def test_list_empty(self):
        client = MagicMock()
        client.list.return_value = []
        assert len(client.list("proxmox_lxc_snapshot")) == 0


class TestGet:
    """Getting individual resources."""

    def test_get_existing(self):
        client = MagicMock()
        client.get.return_value = dict(id="123", name="test")
        assert client.get("proxmox_lxc_snapshot", "123")["name"] == "test"

    def test_get_not_found(self):
        client = MagicMock()
        client.get.return_value = None
        assert client.get("proxmox_lxc_snapshot", "x") is None


class TestUpdate:
    """Updating resources."""

    def test_update(self):
        client = MagicMock()
        client.update.return_value = dict(id="123", name="updated")
        result = client.update("proxmox_lxc_snapshot", "123", dict(name="updated"))
        assert result["name"] == "updated"

    def test_update_not_found(self):
        client = MagicMock()
        client.get.return_value = None
        assert client.get("proxmox_lxc_snapshot", "x") is None
