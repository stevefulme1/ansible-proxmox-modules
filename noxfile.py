# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Nox sessions for stevefulme1.proxmox collection CI."""

from __future__ import annotations

import nox

nox.options.sessions = ["lint", "unit"]
nox.options.reuse_existing_virtualenvs = True


@nox.session(python=["3.12", "3.13"])
def lint(session: nox.Session) -> None:
    """Run linters (pycodestyle + ansible-lint)."""
    session.install("pycodestyle>=2.11", "ansible-lint>=24.2", "ansible-core>=2.16")
    session.run(
        "pycodestyle",
        "--max-line-length=160",
        "--ignore=E402",
        "plugins/modules/",
    )
    session.run(
        "ansible-lint",
        "--profile", "production",
        "plugins/modules/",
    )


@nox.session(python=["3.12", "3.13"])
def unit(session: nox.Session) -> None:
    """Run unit tests with pytest."""
    session.install("-r", "test-requirements.txt")
    session.run(
        "pytest",
        "tests/unit/",
        "-v",
        "--tb=short",
        "--cov=plugins",
        "--cov-report=term-missing",
        *session.posargs,
    )


@nox.session(python="3.12")
def sanity(session: nox.Session) -> None:
    """Run ansible-test sanity checks."""
    session.install("ansible-core>=2.16")
    session.run(
        "ansible-test", "sanity",
        "--python", "3.12",
        "--skip-test", "import",
        "--skip-test", "pylint",
        "--skip-test", "validate-modules",
        "--skip-test", "ansible-doc",
        external=True,
    )


@nox.session(python="3.12")
def import_check(session: nox.Session) -> None:
    """Verify all modules can be imported without errors."""
    session.install("ansible-core>=2.16", "proxmoxer")
    session.run(
        "python", "-c",
        "import importlib, pathlib; "
        "[importlib.import_module(f'plugins.modules.{p.stem}') "
        "for p in pathlib.Path('plugins/modules').glob('*.py') "
        "if p.stem != '__init__']",
    )
