# Security notes

- This is a prototype and is not approved for production use without a security review.
- Keep real secrets in local environment files or the deployment provider's secret manager, never in Git.
- Keep institution records tenant-scoped on the server. Hiding UI elements is not access control.
- Passwords must be hashed; plaintext passwords must never be persisted.
- Use synthetic/fictional institutions and users in demos.
- Restrict CORS to approved frontend origins before deployment.
- Review upload size, accepted file types, storage, malware scanning and authorization before handling real documents.
- Compliance values in sample data are illustrative, not official AICTE policy.
