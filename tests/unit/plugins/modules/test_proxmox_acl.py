# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

"""Tests for proxmox_acl module.

Note: proxmox_acl uses ProxmoxModule but accesses module.params, module.exit_json,
module.check_mode, and module.proxmox_request directly on the ProxmoxModule
instance.  Since ProxmoxModule doesn't expose those (they live on the wrapped
AnsibleModule at self.module), these tests patch proxmox_request onto the
ProxmoxModule class before running the module.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from tests.unit.conftest import set_module_args

MODULE_PATH = (
    "ansible_collections.stevefulme1.proxmox.plugins.modules.proxmox_acl"
)
MODULE_UTILS_PATH = (
    "ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox"
)


def _acl_request_handler(current_acls):
    """Return a side_effect callable simulating proxmox_request for ACL ops."""

    def _handler(method, path, data=None):
        if method == "GET" and path == "access/acl":
            return list(current_acls)
        if method == "PUT" and path == "access/acl":
            return None
        raise ValueError("Unexpected request: %s %s" % (method, path))

    return _handler


def _patch_proxmox_module_for_acl(current_acls):
    """Context manager that adds the attributes proxmox_acl expects on ProxmoxModule.

    The ACL module treats its ProxmoxModule instance as if it were an AnsibleModule:
    it reads .params, .check_mode, .exit_json(), .fail_json(), and .proxmox_request().
    We add lightweight delegation so the module code can run.
    """
    from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
        ProxmoxModule,
    )

    handler = _acl_request_handler(current_acls)

    original_init = ProxmoxModule.__init__

    def _patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        # Expose AnsibleModule attributes directly on self
        self.params = self.module.params
        self.check_mode = self.module.check_mode
        self.exit_json = self.module.exit_json
        self.fail_json = self.module.fail_json
        self.proxmox_request = MagicMock(side_effect=handler)

    return patch.object(ProxmoxModule, "__init__", _patched_init)


def _run_module():
    from ansible_collections.stevefulme1.proxmox.plugins.modules import proxmox_acl

    with pytest.raises(SystemExit) as exc_info:
        proxmox_acl.main()
    return exc_info.value.code


class TestAclAdd:
    """Adding new ACL entries."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_add_user_acl(self, mock_api_cls, module_args):
        mock_api_cls.return_value = MagicMock()

        module_args.update(
            path="/vms/100",
            roles=["PVEAdmin"],
            users=["admin@pve"],
            state="present",
        )
        set_module_args(module_args)

        with _patch_proxmox_module_for_acl(current_acls=[]):
            rc = _run_module()

        assert rc == 0

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_add_group_acl(self, mock_api_cls, module_args):
        mock_api_cls.return_value = MagicMock()

        module_args.update(
            path="/",
            roles=["PVEAuditor"],
            groups=["developers"],
            propagate=True,
            state="present",
        )
        set_module_args(module_args)

        with _patch_proxmox_module_for_acl(current_acls=[]):
            rc = _run_module()

        assert rc == 0


class TestAclRemove:
    """Removing ACL entries."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_remove_acl(self, mock_api_cls, module_args):
        mock_api_cls.return_value = MagicMock()

        module_args.update(
            path="/vms/100",
            roles=["PVEAdmin"],
            users=["admin@pve"],
            state="absent",
        )
        set_module_args(module_args)

        existing_acls = [
            {"path": "/vms/100", "roleid": "PVEAdmin", "ugid": "admin@pve", "type": "user"},
        ]
        with _patch_proxmox_module_for_acl(current_acls=existing_acls):
            rc = _run_module()

        assert rc == 0


class TestAclIdempotent:
    """ACL already exists -- no change."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_acl_already_present(self, mock_api_cls, module_args):
        mock_api_cls.return_value = MagicMock()

        module_args.update(
            path="/vms/100",
            roles=["PVEAdmin"],
            users=["admin@pve"],
            state="present",
        )
        set_module_args(module_args)

        existing_acls = [
            {"path": "/vms/100", "roleid": "PVEAdmin", "ugid": "admin@pve", "type": "user"},
        ]
        with _patch_proxmox_module_for_acl(current_acls=existing_acls):
            rc = _run_module()

        assert rc == 0
