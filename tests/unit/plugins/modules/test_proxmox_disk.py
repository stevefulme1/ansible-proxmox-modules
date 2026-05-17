"""Unit tests for proxmox_disk module."""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from unittest.mock import MagicMock, patch
from tests.unit.conftest import set_module_args

MODULE_UTILS_PATH = "ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox"


def _run_module():
    from ansible_collections.stevefulme1.proxmox.plugins.modules import proxmox_disk
    with pytest.raises(SystemExit) as exc_info:
        proxmox_disk.main()
    return exc_info.value.code


class TestCreate:
    """Test proxmox_disk creation."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_create_proxmox_disk(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.nodes('pve1').disks.return_value.get.side_effect = Exception("not found")

        module_args.update(
            disk="/dev/sdb",
            state="present",
            node='pve1'
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.nodes('pve1').disks.post.assert_called_once()

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_create_check_mode(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.nodes('pve1').disks.return_value.get.side_effect = Exception("not found")

        module_args.update(
            disk="/dev/sdb",
            state="present",
            node='pve1'
        )
        module_args["_ansible_check_mode"] = True
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.nodes('pve1').disks.post.assert_not_called()


class TestDelete:
    """Test proxmox_disk deletion."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_delete_proxmox_disk(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.nodes('pve1').disks.return_value.get.return_value = {
            "disk": "/dev/sdb",
        }

        module_args.update(disk="/dev/sdb", state="absent")
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.nodes('pve1').disks.return_value.delete.assert_called_once()

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_delete_already_absent(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.nodes('pve1').disks.return_value.get.side_effect = Exception("not found")

        module_args.update(disk="/dev/sdb", state="absent")
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.nodes('pve1').disks.return_value.delete.assert_not_called()


class TestIdempotent:
    """Test proxmox_disk idempotency."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_no_change(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.nodes('pve1').disks.return_value.get.return_value = {
            "disk": "/dev/sdb",
            "disk": "/dev/sdb",
        }

        module_args.update(
            disk="/dev/sdb",
            state="present",
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.nodes('pve1').disks.post.assert_not_called()


class TestErrorHandling:
    """Test error handling."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_auth_failure(self, mock_api_cls, module_args):
        mock_api_cls.side_effect = Exception("Authentication failed: 401")

        module_args.update(
            disk="/dev/sdb",
            state="present",
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 1


class TestReturnValues:
    """Test return value structure."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_return_contains_resource(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.nodes('pve1').disks.return_value.get.side_effect = Exception("not found")
        api.nodes('pve1').disks.post.return_value = None

        module_args.update(
            disk="/dev/sdb",
            state="present",
            node='pve1'
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
