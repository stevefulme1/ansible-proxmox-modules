# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

"""Tests for proxmox_mapping_pci module."""

import pytest
from unittest.mock import MagicMock, patch

from tests.unit.conftest import set_module_args

MODULE_PATH = (
    "ansible_collections.stevefulme1.proxmox.plugins.modules.proxmox_mapping_pci"
)
MODULE_UTILS_PATH = (
    "ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox"
)


def _run_module():
    from ansible_collections.stevefulme1.proxmox.plugins.modules import (
        proxmox_mapping_pci,
    )
    with pytest.raises(SystemExit) as exc_info:
        proxmox_mapping_pci.main()
    return exc_info.value.code


class TestCreate:
    """Creating resources."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_create_basic(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api

        module_args.update(state="present", name="test-pci")
        set_module_args(module_args)
        rc = _run_module()
        assert rc == 0


class TestDelete:
    """Deleting resources."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_delete_basic(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api

        module_args.update(state="absent", name="test-pci")
        set_module_args(module_args)
        rc = _run_module()
        assert rc == 0
