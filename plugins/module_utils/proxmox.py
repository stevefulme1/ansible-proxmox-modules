# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


PROXMOX_COMMON_ARGS = dict(
    api_host=dict(type='str', required=True),
    api_user=dict(type='str', required=True),
    api_password=dict(type='str', no_log=True),
    api_token_id=dict(type='str'),
    api_token_secret=dict(type='str', no_log=True),
    validate_certs=dict(type='bool', default=True),
)


class ProxmoxModule(object):
    """Base class wrapping AnsibleModule with Proxmox API connection helpers."""

    def __init__(self, argument_spec, supports_check_mode=True, required_if=None,
                 required_one_of=None, mutually_exclusive=None, required_together=None):
        merged_spec = dict()
        merged_spec.update(PROXMOX_COMMON_ARGS)
        merged_spec.update(argument_spec)

        # Merge required_one_of with the auth requirement
        merged_required_one_of = [
            ['api_password', 'api_token_id'],
        ]
        if required_one_of:
            merged_required_one_of.extend(required_one_of)

        merged_required_together = [
            ['api_token_id', 'api_token_secret'],
        ]
        if required_together:
            merged_required_together.extend(required_together)

        self.module = AnsibleModule(
            argument_spec=merged_spec,
            supports_check_mode=supports_check_mode,
            required_if=required_if,
            required_one_of=merged_required_one_of,
            mutually_exclusive=mutually_exclusive,
            required_together=merged_required_together,
        )

        if not HAS_PROXMOXER:
            self.module.fail_json(msg="proxmoxer library is required. Install it with: pip install proxmoxer")

        self._api = None

    def get_api(self):
        """Return a connected ProxmoxAPI instance, creating one on first call."""
        if self._api is not None:
            return self._api

        params = self.module.params
        auth_args = dict(
            host=params['api_host'],
            user=params['api_user'],
            verify_ssl=params['validate_certs'],
        )

        if params.get('api_token_id') and params.get('api_token_secret'):
            auth_args['token_name'] = params['api_token_id']
            auth_args['token_value'] = params['api_token_secret']
        elif params.get('api_password'):
            auth_args['password'] = params['api_password']

        try:
            self._api = ProxmoxAPI(**auth_args)
        except Exception as e:
            self.module.fail_json(msg="Failed to connect to Proxmox API: %s" % str(e))

        return self._api
