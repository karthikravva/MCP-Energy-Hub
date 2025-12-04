# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of MCP Energy Hub seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to the project maintainers. You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information in your report:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### What to Expect

- A confirmation of your report within 48 hours
- An assessment of the vulnerability and its impact
- A timeline for addressing the vulnerability
- Notification when the vulnerability has been fixed

## Security Best Practices

When using MCP Energy Hub:

### API Keys

- **Never commit API keys** to version control
- Use environment variables or secure secret management
- Rotate API keys periodically
- Use the minimum required permissions

### Deployment

- Keep dependencies up to date
- Use HTTPS in production
- Implement rate limiting for public APIs
- Monitor for unusual activity

### Database

- Use parameterized queries (already implemented via SQLAlchemy)
- Regularly backup your data
- Restrict database access to necessary services only

## Dependencies

We regularly update our dependencies to patch known vulnerabilities. You can check for outdated packages using:

```bash
pip list --outdated
```

## Acknowledgments

We appreciate the security research community's efforts in helping keep MCP Energy Hub and its users safe. Responsible disclosure of vulnerabilities helps us ensure the security and privacy of our users.
