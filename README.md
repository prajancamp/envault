# envault

> Secure local environment variable manager with per-project isolation and audit logs

---

## Installation

```bash
pip install envault
```

Or with pipx for isolated CLI usage:

```bash
pipx install envault
```

---

## Usage

Initialize a vault for your project, then add and load environment variables securely.

```bash
# Initialize a new project vault
envault init

# Store a secret
envault set DATABASE_URL "postgres://user:pass@localhost/mydb"

# Load variables into your shell session
eval $(envault load)

# View stored keys (values are masked)
envault list

# Inspect the audit log
envault log
```

You can also scope variables to specific environments:

```bash
envault set --env production API_KEY "sk-abc123"
envault load --env production
```

Each project maintains its own isolated vault, and every read/write operation is recorded in a tamper-evident audit log stored locally.

---

## Project Structure

```
your-project/
├── .envault/
│   ├── vault.enc      # AES-encrypted secrets
│   └── audit.log      # Append-only audit trail
```

---

## License

This project is licensed under the [MIT License](LICENSE).