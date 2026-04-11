# Ansible Collection — sfulmer.proxmox

Ansible modules for managing [Proxmox VE](https://www.proxmox.com/en/proxmox-virtual-environment) infrastructure. This collection fills critical gaps in Proxmox automation — SDN, firewall, cluster/HA, certificates, identity management, node networking, and notifications — all using the Proxmox REST API via [proxmoxer](https://github.com/proxmoxer/proxmoxer).

## Requirements

- Python >= 3.12
- Ansible >= 2.16
- [proxmoxer](https://pypi.org/project/proxmoxer/) >= 2.0
- [requests](https://pypi.org/project/requests/)

## Installation

```bash
ansible-galaxy collection install sfulmer.proxmox
```

Or from source:

```bash
git clone https://github.com/stevefulme1/ansible-proxmox-modules.git
cd ansible-proxmox-modules
ansible-galaxy collection build
ansible-galaxy collection install sfulmer-proxmox-*.tar.gz
```

## Authentication

All modules support two authentication methods:

**Password authentication:**

```yaml
- name: Create SDN zone
  sfulmer.proxmox.proxmox_sdn_zone:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ vault_proxmox_password }}"
    validate_certs: true
    zone: myzone
    type: vlan
    bridge: vmbr0
    state: present
```

**API token authentication:**

```yaml
- name: Create SDN zone
  sfulmer.proxmox.proxmox_sdn_zone:
    api_host: pve.example.com
    api_user: automation@pve
    api_token_id: ci-token
    api_token_secret: "{{ vault_token_secret }}"
    zone: myzone
    type: vlan
    bridge: vmbr0
    state: present
```

## Modules (20)

### SDN — Software-Defined Networking

| Module | Description |
|--------|-------------|
| `proxmox_sdn_zone` | Manage SDN zones (simple, vlan, vxlan, evpn, qinq) |
| `proxmox_sdn_vnet` | Manage virtual networks within zones |
| `proxmox_sdn_subnet` | Manage subnets and IPAM within VNets |

### Firewall

| Module | Description |
|--------|-------------|
| `proxmox_firewall_rule` | Manage firewall rules at cluster, host, or VM level |
| `proxmox_firewall_ipset` | Manage IP sets for reusable address groups |
| `proxmox_firewall_alias` | Manage named IP/CIDR aliases |
| `proxmox_firewall_group` | Manage security groups (rule collections) |
| `proxmox_firewall_options` | Manage global firewall settings |

### Cluster & High Availability

| Module | Description |
|--------|-------------|
| `proxmox_cluster_info` | Retrieve cluster status, nodes, and resources |
| `proxmox_ha_group` | Manage HA groups with node priorities |
| `proxmox_ha_resource` | Manage HA resource assignments and state |

### Certificates

| Module | Description |
|--------|-------------|
| `proxmox_certificate` | Upload and manage custom TLS certificates per node |
| `proxmox_acme` | Order and renew ACME/Let's Encrypt certificates |

### User & Identity Management

| Module | Description |
|--------|-------------|
| `proxmox_user` | Manage users with realm, groups, and attributes |
| `proxmox_group` | Manage access groups |
| `proxmox_role` | Manage custom roles with privilege sets |
| `proxmox_token` | Manage per-user API tokens |

### Node Networking

| Module | Description |
|--------|-------------|
| `proxmox_node_network` | Manage node network interfaces (bridges, bonds, VLANs) |

### Notifications

| Module | Description |
|--------|-------------|
| `proxmox_notification_endpoint` | Manage notification targets (sendmail, SMTP, Gotify, webhook) |
| `proxmox_notification_matcher` | Manage notification routing rules and filters |

## Usage Examples

### Configure SDN networking

```yaml
- name: Create VLAN zone
  sfulmer.proxmox.proxmox_sdn_zone:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    zone: production
    type: vlan
    bridge: vmbr0
    state: present

- name: Create VNet in zone
  sfulmer.proxmox.proxmox_sdn_vnet:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    vnet: prod-web
    zone: production
    tag: 100
    state: present

- name: Create subnet
  sfulmer.proxmox.proxmox_sdn_subnet:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    subnet: "10.0.100.0/24"
    vnet: prod-web
    gateway: "10.0.100.1"
    snat: true
    state: present
```

### Set up firewall rules

```yaml
- name: Allow SSH from management network
  sfulmer.proxmox.proxmox_firewall_rule:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    scope: cluster
    action: ACCEPT
    type: in
    source: "10.0.0.0/8"
    dport: "22"
    proto: tcp
    comment: "Allow SSH from internal"
    state: present

- name: Create IP set for trusted hosts
  sfulmer.proxmox.proxmox_firewall_ipset:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    name: trusted-hosts
    members:
      - cidr: "10.0.1.0/24"
        comment: "Management subnet"
      - cidr: "10.0.2.5"
        comment: "Jump host"
    state: present
```

### Configure High Availability

```yaml
- name: Create HA group
  sfulmer.proxmox.proxmox_ha_group:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    group: primary-nodes
    nodes:
      - node: pve1
        priority: 3
      - node: pve2
        priority: 2
      - node: pve3
        priority: 1
    restricted: true
    state: present

- name: Add VM to HA
  sfulmer.proxmox.proxmox_ha_resource:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    sid: "vm:100"
    ha_state: started
    group: primary-nodes
    max_restart: 3
    max_relocate: 2
    state: present
```

### Manage users and tokens

```yaml
- name: Create automation user
  sfulmer.proxmox.proxmox_user:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    userid: automation@pve
    password: "{{ automation_password }}"
    groups:
      - admins
    email: automation@example.com
    state: present

- name: Create API token
  sfulmer.proxmox.proxmox_token:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    userid: automation@pve
    tokenid: ci-token
    privsep: false
    state: present
  register: token_result
```

## All modules support

- **Check mode** (`--check`) — preview changes without applying them
- **Idempotency** — only makes changes when the desired state differs from current state
- **Both auth methods** — password or API token

## Development

```bash
# Install dev dependencies
pip install ansible-core>=2.16 ansible-lint>=24.2 pycodestyle>=2.11

# Run linting
pycodestyle --max-line-length=160 --ignore=E402 plugins/modules/*.py
ansible-lint --profile production plugins/modules/*.py

# Run sanity tests (requires collection directory structure)
ansible-test sanity --python 3.12

# Build collection
ansible-galaxy collection build
```

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).
