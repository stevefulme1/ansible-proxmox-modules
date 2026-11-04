# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Tests for backup job retention options."""

import json
from unittest.mock import MagicMock

import pytest

from ansible_collections.stevefulme1.proxmox.plugins.modules import proxmox_backup_job
from tests.unit.conftest import set_module_args


class TestPruneBackups:
    @pytest.fixture
    def api(self, monkeypatch):
        api = MagicMock()
        api.cluster.backup.get.return_value = []
        monkeypatch.setattr(proxmox_backup_job.ProxmoxModule, 'get_api', lambda self: api)
        return api

    @pytest.fixture
    def run_module(self, module_args, capsys):
        def run(params, check_mode=False):
            args = dict(module_args, job_id='daily', storage='local', schedule='02:00',
                        _ansible_check_mode=check_mode)
            args.update(params)
            set_module_args(args)
            with pytest.raises(SystemExit) as exc:
                proxmox_backup_job.main()
            result = json.loads(capsys.readouterr().out)
            assert exc.value.code == (1 if result.get('failed') else 0)
            return result
        return run

    @pytest.mark.parametrize('option', ['prune_backups', 'prune-backups'])
    def test_create(self, api, run_module, option):
        result = run_module({option: 'keep-last=7,keep-weekly=4'})
        assert result['changed']
        api.cluster.backup.post.assert_called_once_with(
            id='daily', storage='local', schedule='02:00',
            **{'prune-backups': 'keep-last=7,keep-weekly=4'}
        )

    @pytest.mark.parametrize('desired, current', [
        ('keep-last=7,keep-weekly=4', {'keep-last': 7, 'keep-weekly': 4}),
        ('keep-weekly=4,keep-last=7', 'keep-last=7,keep-weekly=4'),
        ('keep-last=07', {'keep-last': '7'}),
        ('keep-all=1', {'keep-all': True}),
        ('keep-all=yes', {'keep-all': 1}),
        ('keep-all=off,keep-daily=7', {'keep-all': 0, 'keep-daily': 7}),
    ])
    def test_unchanged_retention_is_idempotent(self, api, run_module, desired, current):
        api.cluster.backup.get.return_value = [
            {'id': 'daily', 'storage': 'local', 'schedule': '02:00', 'prune-backups': current},
        ]
        result = run_module({'prune_backups': desired})
        assert not result['changed']
        api.cluster.backup.return_value.put.assert_not_called()
        api.cluster.backup.post.assert_not_called()

    @pytest.mark.parametrize('current', [None, {'keep-last': 3}, {'keep-last': 7, 'keep-weekly': 4}])
    def test_update_replaces_retention(self, api, run_module, current):
        api.cluster.backup.get.return_value = [
            {'id': 'daily', 'storage': 'local', 'schedule': '02:00', 'prune-backups': current},
        ]
        result = run_module({'prune_backups': 'keep-last=7'})
        assert result['changed']
        api.cluster.backup.return_value.put.assert_called_once_with(**{'prune-backups': 'keep-last=7'})

    @pytest.mark.parametrize('existing', [False, True])
    def test_check_mode_does_not_write(self, api, run_module, existing):
        if existing:
            api.cluster.backup.get.return_value = [
                {'id': 'daily', 'storage': 'local', 'schedule': '02:00', 'prune-backups': {'keep-last': 3}},
            ]
        result = run_module({'prune_backups': 'keep-last=7'}, check_mode=True)
        assert result['changed']
        if existing:
            assert result['changes'] == {'prune-backups': 'keep-last=7'}
        api.cluster.backup.post.assert_not_called()
        api.cluster.backup.return_value.put.assert_not_called()

    def test_omitted_retention_is_preserved(self, api, run_module):
        api.cluster.backup.get.return_value = [
            {'id': 'daily', 'storage': 'local', 'schedule': '02:00', 'prune-backups': {'keep-last': 7}},
        ]
        result = run_module({'enabled': False})
        assert result['changed']
        assert result['job']['prune-backups'] == {'keep-last': 7}
        api.cluster.backup.return_value.put.assert_called_once_with(enabled=0)

    def test_api_validation_error_is_reported(self, api, run_module):
        api.cluster.backup.return_value.put.side_effect = Exception('invalid prune-backups')
        api.cluster.backup.get.return_value = [
            {'id': 'daily', 'storage': 'local', 'schedule': '02:00', 'prune-backups': {'keep-last': 7}},
        ]
        result = run_module({'prune_backups': 'keep-last=invalid'})
        assert result['failed']
        assert 'invalid prune-backups' in result['msg']
