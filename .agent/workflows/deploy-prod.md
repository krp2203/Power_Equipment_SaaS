---
description: Safety-First Deployment from Dev (CT 106) to Production (CT 101)
---

# Production Deployment Workflow (CT 106 → CT 101)

Follow these steps exactly to promote changes from the dev environment to the live site while protecting your data and uptime.

## Phase 1: Preparation (On CT 106 - Dev)

### 1. Final Test
Ensure all features (like FFmpeg compression) are fully working on CT 106.

### 2. Generate Database Migrations
If you modified any models in `app/core/models.py` or elsewhere:
// turbo
```bash
docker compose exec web flask db migrate -m "Description of changes"
```
*Verify the new file in `migrations/versions/`.*

### 3. Commit and Push
// turbo
```bash
git add .
git commit -m "Finalizing features for deployment"
git push origin dev
```

---

## Phase 2: Safety Backup (On CT 101 - Production)

### 4. Create Pre-Deployment Backup
**CRITICAL: Never skip this step.**
// turbo
```bash
./scripts/backup_db.sh
```
*Verify success with: `ls -l backups/latest_backup.sql`.*

---

## Phase 3: Promotion (On CT 101 - Production)

### 5. Sync Code
Merge the `dev` branch into `main`.

// turbo
```bash
git checkout main
git pull origin main
git merge dev
git push origin main
```

### 6. Apply Database Migrations
// turbo
```bash
docker compose exec web flask db upgrade
```

### 7. Update Configuration (.env)
If you added any new variables to `.env` on CT 106, manually add them to CT 101's `.env` now.

### 8. Restart & Verify
// turbo
```bash
docker compose restart web worker
# Check logs for errors
docker compose logs --tail=50
```

---

## Phase 4: Verification

### 9. Site Check
Open the live site and confirm everything is working as expected.

### 10. Sync Dev Back to Main
On CT 106 (Dev), ensure you are back on the `dev` branch and synced with `main`.
// turbo
```bash
git checkout dev
git pull origin main
```
