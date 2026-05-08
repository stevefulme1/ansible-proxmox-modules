# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

"""Tests for ProxmoxModule base class connection logic."""

import json
import pytest
from unittest.mock import MagicMock, patch

from tests.unit.conftest import set_module_args

MODULE_UTILS_PATH = (
    "ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox"
)


class TestProxmoxModulePasswordAuth:
    """Verify ProxmoxModule.get_api() with password authentication."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_password_auth_creates_connection(self, mock_api_cls, module_args):
        set_module_args(module_args)
        from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
            ProxmoxModule,
        )

        pm = ProxmoxModule(argument_spec=dict())
        api = pm.get_api()

        mock_api_cls.assert_called_once()
        call_kwargs = mock_api_cls.call_args[1]
        assert call_kwargs["host"] == "pve1.local"
        assert call_kwargs["user"] == "root@pam"
        assert call_kwargs["password"] == "test"
        assert "token_name" not in call_kwargs
        assert api is mock_api_cls.return_value

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_get_api_returns_cached_instance(self, mock_api_cls, module_args):
        set_module_args(module_args)
        from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
            ProxmoxModule,
        )

        pm = ProxmoxModule(argument_spec=dict())
        first = pm.get_api()
        second = pm.get_api()

        assert first is second
        assert mock_api_cls.call_count == 1


class TestProxmoxModuleTokenAuth:
    """Verify ProxmoxModule.get_api() with API token authentication."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_token_auth_creates_connection(self, mock_api_cls, module_args):
        module_args.update(
            api_password=None,
            api_token_id="mytoken",
            api_token_secret="secret-uuid",
        )
        set_module_args(module_args)
        from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
            ProxmoxModule,
        )

        pm = ProxmoxModule(argument_spec=dict())
        pm.get_api()

        call_kwargs = mock_api_cls.call_args[1]
        assert call_kwargs["token_name"] == "mytoken"
        assert call_kwargs["token_value"] == "secret-uuid"
        assert "password" not in call_kwargs


class TestProxmoxModuleConnectionFailure:
    """Verify graceful handling when ProxmoxAPI raises."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI", side_effect=Exception("conn refused"))
    def test_connection_error_fails_module(self, _mock_api_cls, module_args):
        set_module_args(module_args)
        from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
            ProxmoxModule,
        )

        pm = ProxmoxModule(argument_spec=dict())

        with pytest.raises(SystemExit):
            pm.get_api()


class TestProxmoxModuleMissingLib:
    """Verify error when proxmoxer is not importable."""

    @patch(MODULE_UTILS_PATH + ".HAS_PROXMOXER", False)
    def test_missing_proxmoxer_fails(self, module_args):
        set_module_args(module_args)
        from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
            ProxmoxModule,
        )

        with pytest.raises(SystemExit):
            ProxmoxModule(argument_spec=dict())
