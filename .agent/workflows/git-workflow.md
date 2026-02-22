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
Once changes are tested and verified on CT 106, merge them into `main`.

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
# Restart services if needed
```
