# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r'''
options:
  fail_on_missing:
    description:
      - If C(true), the lookup will fail when a resource is not found.
      - If C(false), missing resources are silently skipped and an empty string is returned.
    type: bool
    default: true
  wantlist:
    description:
      - If C(true), return results as a list even if there is only one match.
      - If C(false), return a comma-separated string of matched IDs.
    type: bool
    default: false
'''
