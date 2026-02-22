---
description: Standard Git workflow for Dev and Production
---

# Git Workflow: CT 106 (Dev) to CT 101 (Prod)

This workflow ensures that development happens safely on CT 106 and is only moved to production after testing.

## 1. Development on CT 106 (Dev)
All work should be done on the `dev` branch.

// turbo
```bash
git checkout dev
git pull origin dev
```

### Making Changes
When you finish a task:
// turbo
```bash
git add .
git commit -m "Description of changes"
git push origin dev
```

## 2. Promoting to CT 101 (Production)
For a safe deployment, follow the **[Safety-First Production Deployment Guide](file:///root/power_equip_saas/.agent/workflows/deploy-prod.md)**. 

### Quick Summary of Promotion:
1.  **On CT 106**: Generate migrations (`flask db migrate`) and push to `origin dev`.
If you made changes to models on Dev:
1.  **On CT 106**: Generate the migration: `flask db migrate -m "Description"`
2.  **Commit**: Git add/commit the new migration file in `migrations/versions/`.
3.  **Deploy**: When you pull on CT 101, run `flask db upgrade`.

### On CT 106 (or Production AG):
// turbo
```bash
git checkout main
git pull origin main
git merge dev
git push origin main
git checkout dev
```

## 3. Updating CT 101 (Production)
Pull the changes onto the live server.
// turbo
```bash
git checkout main
git pull origin main
flask db upgrade  # If there are new migrations
# Restart services if needed
```

## 4. Configuration Synchronization (.env)
Since `.env` is NOT in Git, any changes made on Dev must be manually applied to Production:
1.  **Identify Changes**: Keep track of any new environment variables added during dev.
2.  **Apply to Prod**: Use `scp` or manual edit to update `/root/power_equip_saas/.env` on CT 101.
