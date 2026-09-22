# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Tests for calendar schedules, legacy compatibility, and scheduling guardrails."""

import json
from unittest.mock import MagicMock

import pytest

from ansible_collections.stevefulme1.proxmox.plugins.modules import proxmox_backup_job
from tests.unit.conftest import set_module_args


@pytest.fixture
def run_module(monkeypatch, module_args, capsys):
    api = MagicMock()
    connect = MagicMock(return_value=api)
    monkeypatch.setattr(proxmox_backup_job.ProxmoxModule, 'get_api', connect)

    def run(params, existing=None, check_mode=False):
        api.cluster.backup.get.return_value = [] if existing is None else [existing]
        args = dict(module_args, job_id='daily', storage='local', **{'_ansible_check_mode': check_mode})
        args.update(params)
        set_module_args(args)
        with pytest.raises(SystemExit) as exc:
            proxmox_backup_job.main()
        result = json.loads(capsys.readouterr().out)
        assert exc.value.code == (1 if result.get('failed') else 0)
        return result

    run.api = api
    run.connect = connect
    return run


class TestScheduleCreate:
    @pytest.mark.parametrize('timing', [
        {'schedule': 'mon..fri 02:00'},
    ])
    def test_create(self, run_module, timing):
        result = run_module(timing)
        assert result['changed']
        run_module.api.cluster.backup.post.assert_called_once_with(id='daily', storage='local', **timing)

    @pytest.mark.parametrize('check_mode', [False, True])
    def test_create_requires_schedule(self, run_module, check_mode):
        result = run_module({}, check_mode=check_mode)
        assert result['failed']
        assert 'Either schedule or starttime' in result['msg']
        run_module.api.cluster.backup.post.assert_not_called()


class TestScheduleValidation:
    @pytest.mark.parametrize('timing, message', [
        ({'schedule': 'daily', 'starttime': '02:00'}, 'mutually exclusive'),
        ({'schedule': 'daily', 'dow': 'mon'}, 'mutually exclusive'),
        ({'schedule': 'daily', 'starttime': '02:00', 'dow': 'mon'}, 'mutually exclusive'),
        ({'dow': 'mon'}, 'dow requires starttime'),
        ({'schedule': ''}, 'schedule must not be empty'),
        ({'starttime': '  '}, 'starttime must not be empty'),
        ({'starttime': '02:00', 'dow': ''}, 'dow must not be empty'),
    ])
    def test_invalid_timing_rejected_before_connection(self, run_module, timing, message):
        result = run_module(timing)
        assert result['failed']
        assert message in result['msg']
        run_module.connect.assert_not_called()


class TestScheduleUpdate:
    @pytest.mark.parametrize('timing, current', [
        ({'schedule': 'mon..fri 02:00'}, {'schedule': 'mon..fri 02:00'}),
        ({'starttime': '02:00', 'dow': 'mon,wed'}, {'schedule': 'mon,wed 02:00'}),
        ({'starttime': '02:00'}, {'schedule': '02:00'}),
        ({'starttime': '02:00', 'dow': 'mon,tue,wed,thu,fri,sat,sun'}, {'schedule': '02:00'}),
    ])
    def test_unchanged_schedule_is_idempotent(self, run_module, timing, current):
        result = run_module(timing, dict(id='daily', storage='local', **current))
        assert not result['changed']
        run_module.api.cluster.backup.return_value.put.assert_not_called()
        run_module.api.cluster.backup.post.assert_not_called()

    @pytest.mark.parametrize('timing, current, expected', [
        ({'schedule': '03:00'}, {'schedule': '02:00'}, {'schedule': '03:00'}),
        ({'schedule': '03:00'}, {'starttime': '02:00', 'dow': 'mon'}, {'schedule': '03:00'}),
        ({'starttime': '02:00', 'dow': 'wed'}, {'schedule': 'mon 02:00'}, {'starttime': '02:00', 'dow': 'wed'}),
        ({'starttime': '02:00'}, {'schedule': 'mon 02:00'}, {'starttime': '02:00'}),
    ])
    def test_update_schedule(self, run_module, timing, current, expected):
        result = run_module(timing, dict(id='daily', storage='local', **current))
        assert result['changed']
        run_module.api.cluster.backup.assert_called_once_with('daily')
        run_module.api.cluster.backup.return_value.put.assert_called_once_with(**expected)

    def test_update_without_schedule_preserves_existing(self, run_module):
        result = run_module({'enabled': False}, {'id': 'daily', 'storage': 'local', 'schedule': '02:00', 'enabled': 1})
        assert result['changed']
        assert result['job']['schedule'] == '02:00'
        run_module.api.cluster.backup.return_value.put.assert_called_once_with(enabled=0)


class TestScheduleCheckMode:
    @pytest.mark.parametrize('existing', [None, {'id': 'daily', 'storage': 'local', 'schedule': '02:00'}])
    def test_check_mode_does_not_write(self, run_module, existing):
        result = run_module({'schedule': '03:00'}, existing, check_mode=True)
        assert result['changed']
        run_module.api.cluster.backup.post.assert_not_called()
        run_module.api.cluster.backup.return_value.put.assert_not_called()


class TestLegacyDayNormalization:
    @pytest.mark.parametrize('dow, schedule', [
        ('mon, wed', 'mon,wed 02:00'),
        ('mon;wed', 'mon,wed 02:00'),
        ('  mon\twed\n', 'mon,wed 02:00'),
        (' ,mon;; wed, ', 'mon,wed 02:00'),
        ('mon\0wed', 'mon,wed 02:00'),
        ('mon\0wed\0\0', 'mon,wed 02:00'),
        ('mon; tue; wed; thu; fri; sat; sun', '02:00'),
        ('mon\0tue\0wed\0thu\0fri\0sat\0sun\0', '02:00'),
        ('wed, mon,wed', 'wed,mon,wed 02:00'),
        ('sun,mon,tue,wed,thu,fri,sat', 'sun,mon,tue,wed,thu,fri,sat 02:00'),
    ])
    def test_normalized_schedule_is_idempotent(self, run_module, monkeypatch, dow, schedule):
        # Syslog rejects embedded nulls before the module can process them.
        # Disable invocation logging to exercise Proxmox's legacy separator.
        if '\0' in dow:
            monkeypatch.setattr('ansible.module_utils.basic.AnsibleModule._log_invocation', lambda self: None)
        result = run_module(
            {'starttime': '02:00', 'dow': dow},
            {'id': 'daily', 'storage': 'local', 'schedule': schedule},
        )
        assert not result['changed']
        run_module.api.cluster.backup.return_value.put.assert_not_called()
        run_module.api.cluster.backup.post.assert_not_called()

    def test_changed_schedule_preserves_legacy_payload(self, run_module):
        result = run_module(
            {'starttime': '02:00', 'dow': 'mon; wed'},
            {'id': 'daily', 'storage': 'local', 'schedule': 'mon,wed 03:00'},
        )
        assert result['changed']
        assert result['job']['schedule'] == 'mon,wed 02:00'
        run_module.api.cluster.backup.return_value.put.assert_called_once_with(
            starttime='02:00', dow='mon; wed',
        )
