# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Tests for proxmox_replication module."""

import json
from unittest.mock import MagicMock

import pytest

from ansible_collections.stevefulme1.proxmox.plugins.modules import proxmox_replication
from tests.unit.conftest import set_module_args


@pytest.fixture
def api(monkeypatch):
    api = MagicMock()
    api.cluster.replication.get.return_value = []
    monkeypatch.setattr(proxmox_replication.ProxmoxModule, 'get_api', lambda self: api)
    return api


@pytest.fixture
def run_module(api, module_args, capsys):
    def run(params, check_mode=False):
        args = dict(module_args, rep_id='100-0', target='pve2',
                    _ansible_check_mode=check_mode)
        args.update(params)
        set_module_args(args)
        with pytest.raises(SystemExit) as exc:
            proxmox_replication.main()
        result = json.loads(capsys.readouterr().out)
        assert exc.value.code == (1 if result.get('failed') else 0)
        return result
    return run


class TestCreate:
    def test_create_new_job(self, api, run_module):
        result = run_module({})
        assert result['changed']
        assert 'created' in result['msg']
        api.cluster.replication.post.assert_called_once_with(
            id='100-0', type='local', target='pve2', schedule='*/15',
        )

    def test_create_with_all_params(self, api, run_module):
        result = run_module({'schedule': '*/30', 'rate': 10.0, 'comment': 'test', 'disable': True})
        assert result['changed']
        api.cluster.replication.post.assert_called_once_with(
            id='100-0', type='local', target='pve2', schedule='*/30',
            rate=10.0, comment='test', disable=1,
        )

    def test_create_check_mode(self, api, run_module):
        result = run_module({}, check_mode=True)
        assert result['changed']
        api.cluster.replication.post.assert_not_called()


class TestUpdate:
    def test_no_change_is_idempotent(self, api, run_module):
        api.cluster.replication.get.return_value = [
            {'id': '100-0', 'target': 'pve2', 'schedule': '*/15'},
        ]
        result = run_module({})
        assert not result['changed']
        api.cluster.replication.return_value.put.assert_not_called()

    def test_update_schedule(self, api, run_module):
        api.cluster.replication.get.return_value = [
            {'id': '100-0', 'target': 'pve2', 'schedule': '*/15'},
        ]
        result = run_module({'schedule': '*/30'})
        assert result['changed']
        assert 'updated' in result['msg']

    def test_update_check_mode(self, api, run_module):
        api.cluster.replication.get.return_value = [
            {'id': '100-0', 'target': 'pve2', 'schedule': '*/15'},
        ]
        result = run_module({'schedule': '*/30'}, check_mode=True)
        assert result['changed']
        api.cluster.replication.return_value.put.assert_not_called()


class TestDelete:
    def test_delete_existing(self, api, run_module):
        api.cluster.replication.get.return_value = [
            {'id': '100-0', 'target': 'pve2', 'schedule': '*/15'},
        ]
        result = run_module({'state': 'absent'})
        assert result['changed']
        assert 'deleted' in result['msg']

    def test_delete_nonexistent(self, api, run_module):
        result = run_module({'state': 'absent'})
        assert not result['changed']
        assert 'does not exist' in result['msg']

    def test_delete_with_remove_job_local(self, api, run_module):
        api.cluster.replication.get.return_value = [
            {'id': '100-0', 'target': 'pve2', 'schedule': '*/15'},
        ]
        result = run_module({'state': 'absent', 'remove_job': 'local'})
        assert result['changed']
        api.cluster.replication.return_value.delete.assert_called_once_with(keep=1)

    def test_delete_with_remove_job_full(self, api, run_module):
        api.cluster.replication.get.return_value = [
            {'id': '100-0', 'target': 'pve2', 'schedule': '*/15'},
        ]
        result = run_module({'state': 'absent', 'remove_job': 'full'})
        assert result['changed']
        api.cluster.replication.return_value.delete.assert_called_once_with(keep=0)

    def test_delete_check_mode(self, api, run_module):
        api.cluster.replication.get.return_value = [
            {'id': '100-0', 'target': 'pve2', 'schedule': '*/15'},
        ]
        result = run_module({'state': 'absent'}, check_mode=True)
        assert result['changed']
        api.cluster.replication.return_value.delete.assert_not_called()


class TestErrors:
    def test_create_api_error(self, api, run_module):
        api.cluster.replication.post.side_effect = Exception('connection refused')
        result = run_module({})
        assert result['failed']
        assert 'connection refused' in result['msg']

    def test_update_api_error(self, api, run_module):
        api.cluster.replication.get.return_value = [
            {'id': '100-0', 'target': 'pve2', 'schedule': '*/15'},
        ]
        api.cluster.replication.return_value.put.side_effect = Exception('permission denied')
        result = run_module({'schedule': '*/30'})
        assert result['failed']
        assert 'permission denied' in result['msg']
