# Changelog

All notable changes to **stevefulme1.proxmox** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-05-15

### Added

- PBS backup schedule modules
- Unit tests for 17 modules and integration targets
- Pre-commit and linting configuration
- Pagination to all info modules
- Production-ready roles with real module calls
- Role README.md files for Galaxy import compliance

### Fixed

- Align continuation line indent for E131 in firewall_log and syslog modules
- Remove pycache files from repository
- Add missing role README files
- Resolve Galaxy import validation issues
- Resolve CI failures across lint and sanity

## [2.1.0] - 2026-05-15

### Added

- 76 read-only info modules for full Proxmox VE/PBS API coverage
- 2 EDA source plugins for event-driven automation
- 10 Day-2 operation roles (backup, ceph, cluster, container, firewall, ha, network, node, storage, vm)
- Total: 201 modules, 10 roles, full EDA/inventory coverage

## [2.0.0] - 2026-05-08

### Added

- 12 info modules for VMs, containers, Ceph, HA, firewall, ACLs, and backups
- VM disk resize, APT repository, and cluster join modules
- VM/LXC creation, power control, and inventory plugin
- Comprehensive test suite with unit, integration, and Molecule

### Fixed

- Lookup plugin `doc_fragment` reference: `base_options` to `proxmox`
- CI collection paths for `stevefulme1.proxmox` namespace

## [1.0.1] - 2026-04-11

### Fixed

- Rename `doc_fragment` filename from `base_options.py` to `proxmox.py`
- Remove tarball from tracking and add to `.gitignore`

## [1.0.0] - 2026-04-11

### Added

- 106 modules covering SDN (8), Firewall (7), Storage (4), VM Lifecycle (8), VM Advanced (5), Container (4), Backup (3), Cluster/HA (7), Ceph (7), Certificates (2), Identity (8), Node Management (16), Notifications (2), Resource Management (5), Device Mappings (2), PBS (18)
- Shared `proxmox` module utility with `ProxmoxModule` class
- CI/CD with GitHub Actions (lint, sanity, unit tests, certification)
