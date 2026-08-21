# Ansible Collection — stevefulme1.proxmox

Ansible modules for managing [Proxmox VE](https://www.proxmox.com/en/proxmox-virtual-environment) and [Proxmox Backup Server](https://www.proxmox.com/en/proxmox-backup-server) infrastructure. This collection provides comprehensive automation coverage — SDN, firewall, cluster/HA, certificates, identity management, node networking, notifications, storage, VM/container lifecycle, Ceph, backup/restore, and PBS — all using the Proxmox REST API via [proxmoxer](https://github.com/proxmoxer/proxmoxer).

## Requirements

- Python >= 3.12
- Ansible >= 2.16
- [proxmoxer](https://pypi.org/project/proxmoxer/) >= 2.0
- [requests](https://pypi.org/project/requests/)

## Installation

```bash
ansible-galaxy collection install stevefulme1.proxmox
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
  stevefulme1.proxmox.proxmox_sdn_zone:
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
  stevefulme1.proxmox.proxmox_sdn_zone:
    api_host: pve.example.com
    api_user: automation@pve
    api_token_id: ci-token
    api_token_secret: "{{ vault_token_secret }}"
    zone: myzone
    type: vlan
    bridge: vmbr0
    state: present
```

## Modules (106)

### SDN — Software-Defined Networking (7)

| Module | Description |
|--------|-------------|
| `proxmox_sdn_zone` | Manage SDN zones (simple, vlan, vxlan, evpn, qinq) |
| `proxmox_sdn_vnet` | Manage virtual networks within zones |
| `proxmox_sdn_subnet` | Manage subnets and IPAM within VNets |
| `proxmox_sdn_controller` | Manage SDN controllers (EVPN, BGP) |
| `proxmox_sdn_dns` | Manage SDN DNS integrations (PowerDNS, etc.) |
| `proxmox_sdn_ipam` | Manage SDN IPAM backends (PVE, Netbox, phpIPAM) |
| `proxmox_sdn_dhcp` | Manage SDN DHCP settings |
| `proxmox_sdn_info` | Query SDN running/pending state |

### Firewall (7)

| Module | Description |
|--------|-------------|
| `proxmox_firewall_rule` | Manage firewall rules at cluster, host, or VM level |
| `proxmox_firewall_ipset` | Manage IP sets for reusable address groups |
| `proxmox_firewall_alias` | Manage named IP/CIDR aliases |
| `proxmox_firewall_group` | Manage security groups (rule collections) |
| `proxmox_firewall_options` | Manage global firewall settings |
| `proxmox_firewall_refs_info` | Query available firewall references |
| `proxmox_firewall_log_info` | Query firewall logs (cluster or node level) |

### Storage (4)

| Module | Description |
|--------|-------------|
| `proxmox_storage` | Manage storage definitions (LVM, ZFS, NFS, CIFS, iSCSI, Ceph, PBS, etc.) |
| `proxmox_storage_info` | List/query storage configurations |
| `proxmox_storage_content` | Upload/delete disk images, ISOs, and templates |
| `proxmox_storage_status_info` | Query storage usage and health per node |

### VM Lifecycle (8)

| Module | Description |
|--------|-------------|
| `proxmox_vm_config` | Modify VM hardware (CPU, memory, disks, NICs) |
| `proxmox_vm_snapshot` | Create, delete, or rollback VM snapshots |
| `proxmox_vm_clone` | Clone VMs (full or linked) |
| `proxmox_vm_migrate` | Live/offline migration between nodes |
| `proxmox_vm_template` | Convert VM to template |
| `proxmox_vm_info` | Query VM status and configuration |
| `proxmox_vm_pending_info` | Query pending VM configuration changes |
| `proxmox_vm_pending_apply` | Apply pending VM config changes (reboot) |

### VM Advanced Features (5)

| Module | Description |
|--------|-------------|
| `proxmox_vm_agent` | Execute commands via QEMU guest agent |
| `proxmox_vm_firewall` | Manage per-VM firewall options |
| `proxmox_vm_disk` | Manage individual VM disks (resize, move, import) |
| `proxmox_vm_cloudinit` | Manage cloud-init configuration |
| `proxmox_tag` | Manage VM/container resource tags |

### Container Lifecycle (4)

| Module | Description |
|--------|-------------|
| `proxmox_lxc_config` | Modify LXC container configuration |
| `proxmox_lxc_snapshot` | Create, delete, or rollback container snapshots |
| `proxmox_lxc_clone` | Clone containers |
| `proxmox_lxc_migrate` | Migrate containers between nodes |

### Backup & Restore (3)

| Module | Description |
|--------|-------------|
| `proxmox_backup_job` | Manage scheduled backup jobs |
| `proxmox_backup_info` | Query backup job configurations |
| `proxmox_backup_restore` | Restore VMs/containers from backup |

### Cluster & High Availability (6)

| Module | Description |
|--------|-------------|
| `proxmox_cluster_info` | Retrieve cluster status, nodes, and resources |
| `proxmox_cluster_options` | Manage cluster-wide datacenter options |
| `proxmox_cluster_join_info` | Get cluster join information |
| `proxmox_cluster_metrics` | Configure external metrics servers (Graphite/InfluxDB) |
| `proxmox_cluster_log_info` | Query cluster logs |
| `proxmox_ha_group` | Manage HA groups with node priorities |
| `proxmox_ha_resource` | Manage HA resource assignments and state |

### Ceph (7)

| Module | Description |
|--------|-------------|
| `proxmox_ceph_mon` | Manage Ceph monitors |
| `proxmox_ceph_osd` | Manage Ceph OSDs |
| `proxmox_ceph_pool` | Manage Ceph pools |
| `proxmox_ceph_fs` | Manage CephFS filesystems |
| `proxmox_ceph_mds` | Manage Ceph MDS daemons |
| `proxmox_ceph_mgr` | Manage Ceph manager daemons |
| `proxmox_ceph_info` | Query Ceph cluster status |

### Certificates (2)

| Module | Description |
|--------|-------------|
| `proxmox_certificate` | Upload and manage custom TLS certificates per node |
| `proxmox_acme` | Order and renew ACME/Let's Encrypt certificates |

### User & Identity Management (8)

| Module | Description |
|--------|-------------|
| `proxmox_user` | Manage users with realm, groups, and attributes |
| `proxmox_group` | Manage access groups |
| `proxmox_role` | Manage custom roles with privilege sets |
| `proxmox_token` | Manage per-user API tokens |
| `proxmox_realm` | Manage authentication realms (PAM, LDAP, AD, OpenID) |
| `proxmox_acl` | Manage ACL entries (path-based permissions) |
| `proxmox_tfa` | Manage two-factor authentication |
| `proxmox_permission_info` | Query effective permissions |

### Node Management (14)

| Module | Description |
|--------|-------------|
| `proxmox_node_network` | Manage node network interfaces (bridges, bonds, VLANs) |
| `proxmox_node_network_info` | Query node network interface details |
| `proxmox_node_info` | Query node status (CPU, memory, uptime, version) |
| `proxmox_node_dns` | Manage node DNS settings |
| `proxmox_node_hosts` | Manage /etc/hosts entries |
| `proxmox_node_time` | Manage node timezone |
| `proxmox_node_syslog_info` | Query syslog entries |
| `proxmox_node_apt` | Manage APT repositories |
| `proxmox_node_service` | Manage node services (start/stop/restart) |
| `proxmox_node_disks_info` | Query available physical disks |
| `proxmox_node_disk_init` | Initialize disks (GPT wipe) |
| `proxmox_node_lvm` | Manage LVM volume groups |
| `proxmox_node_zfs` | Manage ZFS pools |
| `proxmox_node_certs_info` | Query node certificate details |
| `proxmox_node_subscription` | Manage node subscription keys |
| `proxmox_node_wake_on_lan` | Trigger Wake-on-LAN for nodes |

### Notifications (2)

| Module | Description |
|--------|-------------|
| `proxmox_notification_endpoint` | Manage notification targets (sendmail, SMTP, Gotify, webhook) |
| `proxmox_notification_matcher` | Manage notification routing rules and filters |

### Resource Management (5)

| Module | Description |
|--------|-------------|
| `proxmox_pool` | Manage resource pools |
| `proxmox_pool_info` | Query pool membership and resources |
| `proxmox_replication` | Manage storage replication jobs |
| `proxmox_vzdump_defaults` | Manage default vzdump backup settings |
| `proxmox_task_info` | Query task status and logs |

### Device Mappings (2)

| Module | Description |
|--------|-------------|
| `proxmox_mapping_pci` | Manage PCI device mappings for passthrough |
| `proxmox_mapping_usb` | Manage USB device mappings for passthrough |

### Proxmox Backup Server (18)

| Module | Description |
|--------|-------------|
| `proxmox_pbs_datastore` | Manage PBS datastores |
| `proxmox_pbs_datastore_info` | Query PBS datastore status and content |
| `proxmox_pbs_namespace` | Manage datastore namespaces |
| `proxmox_pbs_gc` | Run/schedule garbage collection |
| `proxmox_pbs_prune_job` | Manage prune jobs and retention policies |
| `proxmox_pbs_sync_job` | Manage sync jobs between datastores |
| `proxmox_pbs_verify_job` | Manage backup verification jobs |
| `proxmox_pbs_tape_drive` | Manage tape backup drives |
| `proxmox_pbs_tape_media_pool` | Manage tape media pools |
| `proxmox_pbs_tape_backup_job` | Manage tape backup jobs |
| `proxmox_pbs_user` | Manage PBS users |
| `proxmox_pbs_token` | Manage PBS API tokens |
| `proxmox_pbs_acl` | Manage PBS access control |
| `proxmox_pbs_realm` | Manage PBS authentication realms |
| `proxmox_pbs_remote` | Manage remote PBS connections |
| `proxmox_pbs_traffic_control` | Manage bandwidth limits |
| `proxmox_pbs_node_info` | Query PBS node status |
| `proxmox_pbs_metrics` | Configure PBS metrics export |

## Usage Examples

### Configure SDN networking

```yaml
- name: Create VLAN zone
  stevefulme1.proxmox.proxmox_sdn_zone:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    zone: production
    type: vlan
    bridge: vmbr0
    state: present

- name: Create VNet in zone
  stevefulme1.proxmox.proxmox_sdn_vnet:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    vnet: prod-web
    zone: production
    tag: 100
    state: present

- name: Create subnet
  stevefulme1.proxmox.proxmox_sdn_subnet:
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
  stevefulme1.proxmox.proxmox_firewall_rule:
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
  stevefulme1.proxmox.proxmox_firewall_ipset:
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

### Manage storage

```yaml
- name: Add NFS storage
  stevefulme1.proxmox.proxmox_storage:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    storage: nfs-backups
    type: nfs
    server: nas.example.com
    export: /backups
    content:
      - backup
      - iso
    state: present

- name: Upload ISO
  stevefulme1.proxmox.proxmox_storage_content:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    node: pve1
    storage: local
    content_type: iso
    filename: ubuntu-24.04.iso
    source: /tmp/ubuntu-24.04.iso
    state: present
```

### VM lifecycle operations

```yaml
- name: Configure VM hardware
  stevefulme1.proxmox.proxmox_vm_config:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    node: pve1
    vmid: 100
    cores: 4
    memory: 8192
    name: webserver

- name: Take VM snapshot
  stevefulme1.proxmox.proxmox_vm_snapshot:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    node: pve1
    vmid: 100
    snapname: pre-upgrade
    description: "Before OS upgrade"
    state: present

- name: Clone VM
  stevefulme1.proxmox.proxmox_vm_clone:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    node: pve1
    vmid: 100
    newid: 101
    name: webserver-clone
    full: true

- name: Migrate VM to another node
  stevefulme1.proxmox.proxmox_vm_migrate:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    node: pve1
    vmid: 100
    target: pve2
    online: true
```

### Configure High Availability

```yaml
- name: Create HA group
  stevefulme1.proxmox.proxmox_ha_group:
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
  stevefulme1.proxmox.proxmox_ha_resource:
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

### Manage Ceph cluster

```yaml
- name: Create Ceph pool
  stevefulme1.proxmox.proxmox_ceph_pool:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    node: pve1
    name: rbd-pool
    size: 3
    min_size: 2
    pg_autoscale_mode: "on"
    application: rbd
    state: present

- name: Get Ceph status
  stevefulme1.proxmox.proxmox_ceph_info:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    node: pve1
  register: ceph_status
```

### Manage users and tokens

```yaml
- name: Create automation user
  stevefulme1.proxmox.proxmox_user:
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
  stevefulme1.proxmox.proxmox_token:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    userid: automation@pve
    tokenid: ci-token
    privsep: false
    state: present
  register: token_result
```

### Configure Proxmox Backup Server

```yaml
- name: Create PBS datastore
  stevefulme1.proxmox.proxmox_pbs_datastore:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: "{{ pbs_password }}"
    name: backups
    path: /mnt/backups
    gc_schedule: "daily"
    keep_daily: 7
    keep_weekly: 4
    keep_monthly: 6
    state: present

- name: Create sync job
  stevefulme1.proxmox.proxmox_pbs_sync_job:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: "{{ pbs_password }}"
    job_id: sync-offsite
    store: backups
    remote: offsite-pbs
    remote_store: offsite-backups
    schedule: "daily"
    state: present
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
