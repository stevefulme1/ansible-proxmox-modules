# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

"""Shared fixtures for stevefulme1.proxmox unit tests."""

import json
import sys
import types
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Ensure proxmoxer is available even when the real package is not installed.
# This lets tests run in CI environments that lack the SDK.
# ---------------------------------------------------------------------------
if "proxmoxer" not in sys.modules:
    _proxmoxer = types.ModuleType("proxmoxer")
    _proxmoxer.ProxmoxAPI = MagicMock
    sys.modules["proxmoxer"] = _proxmoxer

# ---------------------------------------------------------------------------
# Wire up the ansible_collections namespace package so imports like
#   from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox
# resolve to the local checkout.
# ---------------------------------------------------------------------------
import pathlib  # noqa: E402

_COLLECTION_ROOT = pathlib.Path(__file__).resolve().parents[2]  # tests/unit -> repo root
_NS_PATH = str(_COLLECTION_ROOT)

for _pkg in (
    "ansible_collections",
    "ansible_collections.stevefulme1",
    "ansible_collections.stevefulme1.proxmox",
):
    if _pkg not in sys.modules:
        _mod = types.ModuleType(_pkg)
        _mod.__path__ = [str(_COLLECTION_ROOT / _pkg.replace(".", "/"))]
        _mod.__package__ = _pkg
        sys.modules[_pkg] = _mod

# Point the final namespace at the repo root so plugin imports work
sys.modules["ansible_collections.stevefulme1.proxmox"].__path__ = [str(_COLLECTION_ROOT)]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def module_args():
    """Return a base set of module arguments with common Proxmox connection params."""
    return dict(
        api_host="pve1.local",
        api_user="root@pam",
        api_password="test",
        api_token_id=None,
        api_token_secret=None,
        validate_certs=False,
    )


def _make_chainable_mock():
    """Create a MagicMock that supports proxmoxer's chained attribute access.

    proxmoxer uses ``__getattr__`` and ``__call__`` to build URL paths, e.g.
    ``api.nodes("pve1").network.get()``.  A standard MagicMock already chains
    via ``__getattr__`` but calling the mock (``nodes("pve1")``) returns a *new*
    child mock by default.  We wire it so that ``mock.nodes("pve1")`` returns
    the same child as ``mock.nodes``, keeping the chain predictable.
    """
    mock = MagicMock()

    def _chainable_call(self, *args, **kwargs):  # noqa: ARG001
        return self

    # Patch __call__ on the *class* so every child mock also chains.
    type(mock).__call__ = _chainable_call
    return mock


@pytest.fixture
def mock_proxmox_api():
    """Factory fixture returning a chainable MagicMock mimicking ProxmoxAPI.

    Usage in tests::

        api = mock_proxmox_api()
        api.nodes("pve1").firewall.rules.get.return_value = [...]
    """
    return _make_chainable_mock


@pytest.fixture(autouse=True)
def _reset_ansible_args(monkeypatch):
    """Ensure each test starts with a clean AnsibleModule args state."""
    monkeypatch.delenv("MODULE_COMPLEX_ARGS", raising=False)


def set_module_args(args):
    """Inject *args* so AnsibleModule.__init__ reads them from stdin.

    Mirrors the helper used by ansible-core's own unit-test suite.
    Supports both ansible-core <2.20 (plain _ANSIBLE_ARGS) and >=2.20
    (requires _ANSIBLE_PROFILE serialization profile).
    """
    args = json.dumps({"ANSIBLE_MODULE_ARGS": args})
    from ansible.module_utils import basic as _basic

    _basic._ANSIBLE_ARGS = args.encode("utf-8")

    # ansible-core >= 2.20 requires a serialization profile
    if hasattr(_basic, "_ANSIBLE_PROFILE"):
        _basic._ANSIBLE_PROFILE = "legacy"
