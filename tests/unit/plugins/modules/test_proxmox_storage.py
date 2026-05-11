# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

"""Tests for proxmox_storage module."""

import pytest
from unittest.mock import MagicMock, patch

from tests.unit.conftest import set_module_args

MODULE_UTILS_PATH = (
    "ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox"
)


def _run_module():
    from ansible_collections.stevefulme1.proxmox.plugins.modules import proxmox_storage

    with pytest.raises(SystemExit) as exc_info:
        proxmox_storage.main()
    return exc_info.value.code


class TestStorageCreateDirectory:
    """Creating directory-type storage."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_create_dir_storage(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        # storage not found
        api.storage.return_value.get.side_effect = Exception("not found")

        module_args.update(
            storage="local-images",
            type="dir",
            path="/mnt/images",
            content=["images", "iso"],
            state="present",
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.storage.post.assert_called_once()
        call_kwargs = api.storage.post.call_args[1]
        assert call_kwargs["storage"] == "local-images"
        assert call_kwargs["type"] == "dir"
        assert call_kwargs["path"] == "/mnt/images"
        assert call_kwargs["content"] == "images,iso"


class TestStorageCreateNFS:
    """Creating NFS storage."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_create_nfs_storage(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.storage.return_value.get.side_effect = Exception("not found")

        module_args.update(
            storage="nfs-backup",
            type="nfs",
            server="192.168.1.100",
            export="/mnt/backup",
            content=["backup", "iso"],
            state="present",
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        call_kwargs = api.storage.post.call_args[1]
        assert call_kwargs["type"] == "nfs"
        assert call_kwargs["server"] == "192.168.1.100"
        assert call_kwargs["export"] == "/mnt/backup"


class TestStorageCreateCIFS:
    """Creating CIFS storage."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_create_cifs_storage(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.storage.return_value.get.side_effect = Exception("not found")

        module_args.update(
            storage="smb-share",
            type="cifs",
            server="fileserver.local",
            content=["backup"],
            state="present",
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        call_kwargs = api.storage.post.call_args[1]
        assert call_kwargs["type"] == "cifs"
        assert call_kwargs["server"] == "fileserver.local"


class TestStorageDelete:
    """Removing an existing storage definition."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_delete_storage(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.storage.return_value.get.return_value = {
            "storage": "nfs-backup",
            "type": "nfs",
        }

        module_args.update(storage="nfs-backup", state="absent")
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.storage.return_value.delete.assert_called_once()


class TestStorageIdempotent:
    """Storage already exists with matching config."""

    @patch(MODULE_UTILS_PATH + ".ProxmoxAPI")
    def test_no_change(self, mock_api_cls, module_args):
        api = MagicMock()
        mock_api_cls.return_value = api
        api.storage.return_value.get.return_value = {
            "storage": "local-images",
            "type": "dir",
            "path": "/mnt/images",
            "content": "images,iso",
        }

        module_args.update(
            storage="local-images",
            type="dir",
            path="/mnt/images",
            content=["images", "iso"],
            state="present",
        )
        set_module_args(module_args)
        rc = _run_module()

        assert rc == 0
        api.storage.post.assert_not_called()
