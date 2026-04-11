# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this collection, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please send details to the maintainers via:

- **Email:** Open a [private security advisory](https://github.com/stevefulme1/ansible-proxmox-modules/security/advisories/new) on GitHub

Please include:

- A description of the vulnerability
- Steps to reproduce the issue
- Affected module(s) and version(s)
- Any potential impact assessment

## Response Timeline

- **Acknowledgment:** Within 48 hours of report
- **Initial assessment:** Within 5 business days
- **Fix and disclosure:** Coordinated with the reporter

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |

## Security Best Practices

When using this collection:

- Store credentials using Ansible Vault or a secrets manager (HashiCorp Vault, etc.)
- Use API tokens with minimal required privileges instead of root passwords
- Always set `validate_certs: true` in production environments
- Restrict access to playbooks containing Proxmox credentials
- Rotate API tokens regularly
