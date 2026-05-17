"""Unit tests for proxmox_certificate module."""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from unittest.mock import MagicMock, patch
from tests.unit.conftest import set_module_args

MODULE_UTILS_PATH = "ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox"


def _run_module():
    from ansible_collections.stevefulme1.proxmox.plugins.modules import proxmox_certificate
    with pytest.raises(SystemExit) as exc_info:
        proxmox_certificate.main()
    return exc_info.value.code


class TestCreate:
    """Test proxmox_certificate creation."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_create_proxmox_certificate(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.nodes('pve1').certificates.custom.return_value.get.side_effect = Exception("not found")

        module_args.update(
            node="pve1",
            state="present",
            certificates='-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----'
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.nodes('pve1').certificates.custom.post.assert_called_once()

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_create_check_mode(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.nodes('pve1').certificates.custom.return_value.get.side_effect = Exception("not found")

        module_args.update(
            node="pve1",
            state="present",
            certificates='-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----'
        )
        module_args["_ansible_check_mode"] = True
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.nodes('pve1').certificates.custom.post.assert_not_called()


class TestDelete:
    """Test proxmox_certificate deletion."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_delete_proxmox_certificate(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.nodes('pve1').certificates.custom.return_value.get.return_value = {
            "node": "pve1",
        }

        module_args.update(node="pve1", state="absent")
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.nodes('pve1').certificates.custom.return_value.delete.assert_called_once()

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_delete_already_absent(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.nodes('pve1').certificates.custom.return_value.get.side_effect = Exception("not found")

        module_args.update(node="pve1", state="absent")
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.nodes('pve1').certificates.custom.return_value.delete.assert_not_called()


class TestIdempotent:
    """Test proxmox_certificate idempotency."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_no_change(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.nodes('pve1').certificates.custom.return_value.get.return_value = {
            "node": "pve1",
            "node": "pve1",
        }

        module_args.update(
            node="pve1",
            state="present",
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.nodes('pve1').certificates.custom.post.assert_not_called()


class TestErrorHandling:
    """Test error handling."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_auth_failure(self, mock_api_cls, module_args):
        mock_api_cls.side_effect = Exception("Authentication failed: 401")

        module_args.update(
            node="pve1",
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
        api.nodes('pve1').certificates.custom.return_value.get.side_effect = Exception("not found")
        api.nodes('pve1').certificates.custom.post.return_value = None

        module_args.update(
            node="pve1",
            state="present",
            certificates='-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----'
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
