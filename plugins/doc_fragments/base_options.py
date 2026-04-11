# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r'''
options:
  api_host:
    description:
      - The hostname or IP address of the Proxmox VE API server.
    type: str
    required: true
    env:
      - name: PROXMOX_HOST
  api_user:
    description:
      - The user name to authenticate with (e.g. C(root@pam), C(admin@pve)).
    type: str
    required: true
    env:
      - name: PROXMOX_USER
  api_password:
    description:
      - The password for the API user.
      - Mutually exclusive with I(api_token_id) and I(api_token_secret).
    type: str
    env:
      - name: PROXMOX_PASSWORD
  api_token_id:
    description:
      - The API token ID for token-based authentication.
      - Must be used together with I(api_token_secret).
    type: str
    env:
      - name: PROXMOX_TOKEN_ID
  api_token_secret:
    description:
      - The API token secret value.
      - Must be used together with I(api_token_id).
    type: str
    env:
      - name: PROXMOX_TOKEN_SECRET
  validate_certs:
    description:
      - Whether to validate SSL/TLS certificates.
      - Set to C(false) for self-signed certificates.
    type: bool
    default: true
    env:
      - name: PROXMOX_VALIDATE_CERTS
'''
