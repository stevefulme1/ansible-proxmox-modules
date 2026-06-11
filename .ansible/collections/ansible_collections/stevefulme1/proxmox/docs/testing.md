# Testing Guide -- stevefulme1.proxmox

This document covers all test layers for the collection: unit, integration,
molecule, and CI.

---

## Prerequisites

```bash
pip install -r test-requirements.txt
```

Test requirements: `pytest`, `pytest-cov`, `proxmoxer`, `ansible-core>=2.16`.

---

## Unit tests

Unit tests mock the Proxmox API via `unittest.mock` and run entirely offline.
No Proxmox host is needed.

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ -v --cov=plugins --cov-report=term-missing

# Run a single test file
pytest tests/unit/plugins/modules/test_proxmox_firewall_rule.py -v
```

### Test structure

```
tests/unit/
  conftest.py                          # Shared fixtures, proxmoxer mock, namespace wiring
  plugins/modules/
    test_proxmox_base.py               # ProxmoxModule connection logic
    test_proxmox_firewall_rule.py      # Firewall rule CRUD
    test_proxmox_sdn_zone.py           # SDN zone lifecycle
    test_proxmox_node_network.py       # Network interface config
    test_proxmox_storage.py            # Storage pool management
    test_proxmox_acl.py                # ACL entry management
```

### Writing new unit tests

1. Import `set_module_args` from `tests.unit.conftest`.
2. Patch `ProxmoxAPI` at the module_utils level (or directly if the module
   imports it).
3. Call `set_module_args(...)` with module parameters.
4. Run the module's `main()` inside `pytest.raises(SystemExit)`.
5. Assert on the mock API calls and exit code.

---

## Integration tests

Integration tests require a live Proxmox VE API endpoint.

### Setup

1. Copy the template:
   ```bash
   cp tests/integration/cloud-config-proxmox.ini.template \
      tests/integration/cloud-config-proxmox.ini
   ```
2. Fill in your Proxmox credentials.
3. Export the variables or set them in your environment.

### Running

```bash
# Run all integration targets
ansible-test integration --python 3.12 --allow-unsupported \
    proxmox_node_info proxmox_firewall_rule proxmox_sdn_zone \
    proxmox_storage proxmox_acl

# Run a single target
ansible-test integration --python 3.12 --allow-unsupported proxmox_node_info
```

### Available targets

| Target                     | Description             | Destructive |
|----------------------------|-------------------------|-------------|
| `proxmox_node_info`        | Read-only node status   | No          |
| `proxmox_firewall_rule`    | Firewall rule CRUD      | Yes         |
| `proxmox_sdn_zone`         | SDN zone lifecycle      | Yes         |
| `proxmox_storage`          | Storage pool management | Yes         |
| `proxmox_acl`              | ACL entry lifecycle     | Yes         |

---

## Molecule

Molecule provides an end-to-end workflow using a delegated driver that
targets a Proxmox API directly.

```bash
# Set credentials
export PROXMOX_API_HOST=pve1.example.com
export PROXMOX_API_USER=root@pam
export PROXMOX_API_PASSWORD=changeme

# Full lifecycle
molecule test -s default

# Just converge + verify
molecule converge -s default
molecule verify -s default
```

---

## Nox sessions

[nox](https://nox.thea.codes/) is configured as an alternative runner:

```bash
# List available sessions
nox -l

# Run linters
nox -s lint

# Run unit tests
nox -s unit

# Run sanity checks
nox -s sanity

# Verify all modules import cleanly
nox -s import_check
```

---

## CI pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs automatically
on push and PR to `main`:

| Job                  | Trigger            | Description                                     |
|----------------------|--------------------|-------------------------------------------------|
| `ansible-lint`       | push / PR          | pycodestyle + ansible-lint                      |
| `sanity`             | push / PR          | ansible-test sanity (matrix: ansible + python)  |
| `unit`               | push / PR          | pytest unit tests (matrix: python 3.12, 3.13)   |
| `integration-mock`   | push / PR          | Integration targets in check mode               |
| `integration-cloud`  | workflow_dispatch  | Integration against live Proxmox (needs secrets)|

### Required secrets for cloud integration

Set these in your GitHub repository settings:

- `PROXMOX_API_HOST` -- Proxmox VE hostname or IP
- `PROXMOX_API_USER` -- API user (e.g. `root@pam`)
- `PROXMOX_API_PASSWORD` -- API password
- `PROXMOX_TEST_NODE` -- Node name for node-specific tests (default: `pve1`)
