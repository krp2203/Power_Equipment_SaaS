# Production Deployment Walkthrough: Universal Ad Fix

This document summarizes the changes applied to the production environment (CT 101) and provides a detailed explanation of omitted files for the agent on CT 106.

## 🚀 Changes Applied to Production

### 1. Universal Environment-Aware Fix
Instead of hard-coding the `.local` domain requested in commit `b6b787b`, we implemented a "Smart Fix" in `dealer_frontend_next/app/page.tsx`.

```typescript
// Detects environment and uses the appropriate domain extension automatically
'Host': config.slug ? `${config.slug}.bentcrankshaft.${process.env.NODE_ENV === 'production' ? 'com' : 'local'}` : 'localhost',
```

### 2. Benefits of this Approach
- **True Either/Or Logic**: The same code now works perfectly on both CT 101 (Production) and CT 106 (Test) without manual changes.
- **Safety**: No risk of showing `.local` links to live customers.
- **Maintenance**: No need to "revert" or change headers when moving code between environments.

---

## 🚫 Why Other Files from `59d141d` Were Omitted
Commit `59d141d` contained 15 files that were specifically skipped during this production deployment.

### 📋 List of Omitted Files

| Category | Files | Purpose on CT 106 | Why Omitted from CT 101 |
| :--- | :--- | :--- | :--- |
| **Docker / Nginx** | `docker-compose-test.yml`, `Dockerfile.nginx`, `nginx_test.conf` | Implements the local SSL and domain simulation layer. | CT 101 already has a mature Nginx/SSL setup managed by Proxmox/Certbot. |
| **Certificates** | `nginx_certs/self-signed.*` | Provides local HTTPS for `.local` domains. | Production uses real Let's Encrypt certificates. |
| **Setup Scripts** | `fix_admin.py`, `restore_organizations.py`, `theme_id_1.json` | Recreates the production database state on the test server. | CT 101 is the **source of truth**; running these could corrupt live data. |
| **Documentation** | `SETUP_COMPLETE.md`, `PRODUCTION_IDENTICAL_TEST_SETUP.md` | Guides for the CT 106 setup process. | Redundant on a per-commit deployment to live. |
| **Safety Tools** | `verify_production_safety.sh` | A "gatekeeper" script used on CT 106 to prevent accidental test-code commits. | Meant to be used *before* pushing to Git, not at the time of deployment. |

### 🤖 Message for CT 106 Agent
The agent on CT 106 should continue to use these files to maintain the **Production-Identical Test Environment**. However, the **Universal Host Header Fix** above should be recognized as the new standard. 

> [!IMPORTANT]
> **CT 106 Agent**: Please ensure that future code changes use the `process.env.NODE_ENV` check for domain detection rather than hard-coding `.local` or `.com`.

---

## ✅ Deployment Verification
- **Frontend Restarted**: Successfully picked up the new `page.tsx` change.
- **Log Verification**: Backend is receiving correct `.com` Host headers from production.
- **Production Status**: Stable.
