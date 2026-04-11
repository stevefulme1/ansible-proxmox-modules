# Changelog

All notable changes to this collection will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] — 2026-04-11

### Added

#### Module Utilities
- `proxmox` — Base module utility with `ProxmoxModule` class wrapping proxmoxer authentication and connection handling.

#### SDN — Software-Defined Networking (8 modules)
- `proxmox_sdn_zone` — Manage SDN zones (simple, vlan, vxlan, evpn, qinq).
- `proxmox_sdn_vnet` — Manage virtual networks within zones.
- `proxmox_sdn_subnet` — Manage subnets and IPAM within VNets.
- `proxmox_sdn_controller` — Manage SDN controllers (EVPN, BGP).
- `proxmox_sdn_dns` — Manage SDN DNS integrations (PowerDNS, etc.).
- `proxmox_sdn_ipam` — Manage SDN IPAM backends (PVE, Netbox, phpIPAM).
- `proxmox_sdn_dhcp` — Manage SDN DHCP settings.
- `proxmox_sdn_info` — Query SDN running/pending state.

#### Firewall (7 modules)
- `proxmox_firewall_rule` — Manage firewall rules at cluster, host, or VM level.
- `proxmox_firewall_ipset` — Manage IP sets for reusable address groups.
- `proxmox_firewall_alias` — Manage named IP/CIDR aliases.
- `proxmox_firewall_group` — Manage security groups (rule collections).
- `proxmox_firewall_options` — Manage global firewall settings.
- `proxmox_firewall_refs_info` — Query available firewall references.
- `proxmox_firewall_log_info` — Query firewall logs.

#### Storage (4 modules)
- `proxmox_storage` — Manage storage definitions (LVM, ZFS, NFS, CIFS, iSCSI, Ceph, PBS, etc.).
- `proxmox_storage_info` — List/query storage configurations.
- `proxmox_storage_content` — Upload/delete disk images, ISOs, and templates.
- `proxmox_storage_status_info` — Query storage usage and health per node.

#### VM Lifecycle (8 modules)
- `proxmox_vm_config` — Modify VM hardware (CPU, memory, disks, NICs).
- `proxmox_vm_snapshot` — Create, delete, or rollback VM snapshots.
- `proxmox_vm_clone` — Clone VMs (full or linked).
- `proxmox_vm_migrate` — Live/offline migration between nodes.
- `proxmox_vm_template` — Convert VM to template.
- `proxmox_vm_info` — Query VM status and configuration.
- `proxmox_vm_pending_info` — Query pending VM configuration changes.
- `proxmox_vm_pending_apply` — Apply pending VM config changes.

#### VM Advanced Features (5 modules)
- `proxmox_vm_agent` — Execute commands via QEMU guest agent.
- `proxmox_vm_firewall` — Manage per-VM firewall options.
- `proxmox_vm_disk` — Manage individual VM disks (resize, move, import).
- `proxmox_vm_cloudinit` — Manage cloud-init configuration.
- `proxmox_tag` — Manage VM/container resource tags.

#### Container Lifecycle (4 modules)
- `proxmox_lxc_config` — Modify LXC container configuration.
- `proxmox_lxc_snapshot` — Create, delete, or rollback container snapshots.
- `proxmox_lxc_clone` — Clone containers.
- `proxmox_lxc_migrate` — Migrate containers between nodes.

#### Backup & Restore (3 modules)
- `proxmox_backup_job` — Manage scheduled backup jobs.
- `proxmox_backup_info` — Query backup job configurations.
- `proxmox_backup_restore` — Restore VMs/containers from backup.

#### Cluster & High Availability (7 modules)
- `proxmox_cluster_info` — Retrieve cluster status, nodes, and resources.
- `proxmox_cluster_options` — Manage cluster-wide datacenter options.
- `proxmox_cluster_join_info` — Get cluster join information.
- `proxmox_cluster_metrics` — Configure external metrics servers.
- `proxmox_cluster_log_info` — Query cluster logs.
- `proxmox_ha_group` — Manage HA groups with node priorities.
- `proxmox_ha_resource` — Manage HA resource assignments and state.

#### Ceph (7 modules)
- `proxmox_ceph_mon` — Manage Ceph monitors.
- `proxmox_ceph_osd` — Manage Ceph OSDs.
- `proxmox_ceph_pool` — Manage Ceph pools.
- `proxmox_ceph_fs` — Manage CephFS filesystems.
- `proxmox_ceph_mds` — Manage Ceph MDS daemons.
- `proxmox_ceph_mgr` — Manage Ceph manager daemons.
- `proxmox_ceph_info` — Query Ceph cluster status.

#### Certificates (2 modules)
- `proxmox_certificate` — Upload and manage custom TLS certificates per node.
- `proxmox_acme` — Order and renew ACME/Let's Encrypt certificates.

#### User & Identity Management (8 modules)
- `proxmox_user` — Manage users with realm, groups, and attributes.
- `proxmox_group` — Manage access groups.
- `proxmox_role` — Manage custom roles with privilege sets.
- `proxmox_token` — Manage per-user API tokens.
- `proxmox_realm` — Manage authentication realms (PAM, LDAP, AD, OpenID).
- `proxmox_acl` — Manage ACL entries (path-based permissions).
- `proxmox_tfa` — Manage two-factor authentication.
- `proxmox_permission_info` — Query effective permissions.

#### Node Management (16 modules)
- `proxmox_node_network` — Manage node network interfaces.
- `proxmox_node_network_info` — Query node network interface details.
- `proxmox_node_info` — Query node status.
- `proxmox_node_dns` — Manage node DNS settings.
- `proxmox_node_hosts` — Manage /etc/hosts entries.
- `proxmox_node_time` — Manage node timezone.
- `proxmox_node_syslog_info` — Query syslog entries.
- `proxmox_node_apt` — Manage APT repositories.
- `proxmox_node_service` — Manage node services.
- `proxmox_node_disks_info` — Query available physical disks.
- `proxmox_node_disk_init` — Initialize disks (GPT wipe).
- `proxmox_node_lvm` — Manage LVM volume groups.
- `proxmox_node_zfs` — Manage ZFS pools.
- `proxmox_node_certs_info` — Query node certificate details.
- `proxmox_node_subscription` — Manage node subscription keys.
- `proxmox_node_wake_on_lan` — Trigger Wake-on-LAN for nodes.

#### Notifications (2 modules)
- `proxmox_notification_endpoint` — Manage notification targets.
- `proxmox_notification_matcher` — Manage notification routing rules.

#### Resource Management (5 modules)
- `proxmox_pool` — Manage resource pools.
- `proxmox_pool_info` — Query pool membership and resources.
- `proxmox_replication` — Manage storage replication jobs.
- `proxmox_vzdump_defaults` — Manage default vzdump backup settings.
- `proxmox_task_info` — Query task status and logs.

#### Device Mappings (2 modules)
- `proxmox_mapping_pci` — Manage PCI device mappings for passthrough.
- `proxmox_mapping_usb` — Manage USB device mappings for passthrough.

#### Proxmox Backup Server (18 modules)
- `proxmox_pbs_datastore` — Manage PBS datastores.
- `proxmox_pbs_datastore_info` — Query PBS datastore status and content.
- `proxmox_pbs_namespace` — Manage datastore namespaces.
- `proxmox_pbs_gc` — Run/schedule garbage collection.
- `proxmox_pbs_prune_job` — Manage prune jobs and retention policies.
- `proxmox_pbs_sync_job` — Manage sync jobs between datastores.
- `proxmox_pbs_verify_job` — Manage backup verification jobs.
- `proxmox_pbs_tape_drive` — Manage tape backup drives.
- `proxmox_pbs_tape_media_pool` — Manage tape media pools.
- `proxmox_pbs_tape_backup_job` — Manage tape backup jobs.
- `proxmox_pbs_user` — Manage PBS users.
- `proxmox_pbs_token` — Manage PBS API tokens.
- `proxmox_pbs_acl` — Manage PBS access control.
- `proxmox_pbs_realm` — Manage PBS authentication realms.
- `proxmox_pbs_remote` — Manage remote PBS connections.
- `proxmox_pbs_traffic_control` — Manage bandwidth limits.
- `proxmox_pbs_node_info` — Query PBS node status.
- `proxmox_pbs_metrics` — Configure PBS metrics export.
