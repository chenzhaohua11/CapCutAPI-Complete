# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please follow these steps:

1. **Do not** open a public issue
2. Email security concerns to: [security@capcutapi.com](mailto:security@capcutapi.com)
3. Include a detailed description of the vulnerability
4. Provide steps to reproduce the issue if possible
5. Allow reasonable time for response before public disclosure

## Security Best Practices

### Configuration Security
- Never commit sensitive credentials to version control
- Use environment variables for configuration
- Implement proper input validation
- Use HTTPS in production
- Enable CORS appropriately

### API Security
- Rate limiting is implemented (100 requests/hour by default)
- Input sanitization for all endpoints
- SQL injection prevention (using parameterized queries)
- XSS protection headers
- Content-Type validation

### File Upload Security
- File type validation (whitelist allowed types)
- File size limits
- Malware scanning (when possible)
- Secure file storage
- Path traversal prevention

### Dependencies
- Regular security updates
- Automated dependency scanning
- Security advisories monitoring
- Minimal dependency footprint

## Security Scanning

This project uses several security tools:

- **Bandit**: Python security linter
- **Safety**: Dependency vulnerability scanner
- **Pre-commit hooks**: Automated security checks
- **GitHub Security Advisories**: Dependency monitoring

Run security scans locally:

```bash
# Install security tools
pip install bandit safety

# Run security scan
bandit -r . -f json -o bandit-report.json

# Check dependencies
safety check
```

## Security Headers

The application includes these security headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

## Environment Security

### Production Checklist
- [ ] Environment variables configured
- [ ] Debug mode disabled
- [ ] HTTPS enabled
- [ ] Rate limiting active
- [ ] Logging configured
- [ ] Error handling in place
- [ ] Security headers enabled
- [ ] Dependencies updated
- [ ] Secrets rotated
- [ ] Access logs monitored