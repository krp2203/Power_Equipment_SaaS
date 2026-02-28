# Production-Identical Test Environment Setup

**Goal:** Replicate production (CT 101) multi-tenancy on CT 106 test environment

**What You'll Get:**
- ✅ nginx proxy handling multi-tenancy (like production)
- ✅ Subdomain routing to different organizations
- ✅ All three dealers showing correct branding
- ✅ No workarounds needed
- ✅ Safe to test features before production deployment

---

## 📋 SETUP INSTRUCTIONS

### Step 1: Stop Current Environment

```bash
cd /root/power_equip_saas_test

# Stop quick environment (if running)
docker compose -f docker-compose.quick.yml down

# Verify everything stopped
docker ps
# Should show no containers
```

### Step 2: Update /etc/hosts

Add these lines to `/etc/hosts`:

```bash
# For localhost testing
127.0.0.1 bentcrankshaft.local demo.bentcrankshaft.local
127.0.0.1 kens-mowers.bentcrankshaft.local
127.0.0.1 ncpower.bentcrankshaft.local
```

**How to edit:**
```bash
sudo nano /etc/hosts
# Add the lines above
# Ctrl+O (save), Ctrl+X (exit)

# Or one-liner:
echo "127.0.0.1 bentcrankshaft.local demo.bentcrankshaft.local kens-mowers.bentcrankshaft.local ncpower.bentcrankshaft.local" | sudo tee -a /etc/hosts
```

### Step 3: Start Production-Identical Environment

```bash
# Start with the new docker-compose-test.yml (includes nginx)
docker compose -f docker-compose-test.yml up -d

# Wait for containers to stabilize (first time: 2-3 minutes)
# Watch progress:
docker compose -f docker-compose-test.yml logs -f

# Press Ctrl+C when you see "ready in 600ms" from Next.js
```

### Step 4: Verify All Containers

```bash
docker compose -f docker-compose-test.yml ps

# Should show 7 containers, all "Up":
# NAME                           STATUS
# power_equip_saas_test-db-1     Up (healthy)
# power_equip_saas_test-redis-1  Up (healthy)
# power_equip_saas_test-web-1    Up (healthy)
# power_equip_saas_test-worker-1 Up
# power_equip_saas_test-beat-1   Up
# power_equip_saas_test-frontend-1 Up
# power_equip_saas_test-nginx-1  Up
```

---

## 🧪 TESTING MULTI-TENANCY

### Test 1: Verify nginx is proxying correctly

```bash
# Root domain (Master org - Demo Dealer)
curl -s http://bentcrankshaft.local | grep -o "<title>.*</title>"
# Should show: <title>Power Equipment Dealer</title>

# Check backend sees correct Host header
curl -s http://bentcrankshaft.local/api/v1/site-info | python3 -m json.tool | grep -A5 '"identity"'
# Should show: "name": "Demo Dealer"
```

### Test 2: Verify Ken's Mowers subdomain

```bash
# Ken's Mowers subdomain
curl -s http://kens-mowers.bentcrankshaft.local/api/v1/site-info | python3 -m json.tool | grep -A5 '"identity"'
# Should show: "name": "Ken's Mowers"
# Should show: "primaryColor": "#288a2f"
```

### Test 3: Verify NC Power subdomain

```bash
# NC Power subdomain
curl -s http://ncpower.bentcrankshaft.local/api/v1/site-info | python3 -m json.tool | grep -A5 '"identity"'
# Should show: "name": "NC Power Equipment Inc."
```

### Test 4: View in Browser

Open these URLs:

1. **Master Org (Demo Dealer):**
   - http://bentcrankshaft.local

2. **Ken's Mowers:**
   - http://kens-mowers.bentcrankshaft.local

3. **NC Power:**
   - http://ncpower.bentcrankshaft.local

**Expected:**
- Each shows correct logo in hero section
- Header shows correct organization name
- Colors are correct for each dealer

---

## 🔄 HOW IT WORKS

```
User Browser
    ↓
http://kens-mowers.bentcrankshaft.local
    ↓
nginx (Port 80)
    ↓ (recognizes subdomain, checks route rules)
    ├─ Is it /api? → Forward to Flask backend (port 8005)
    │  Backend sees: Host: kens-mowers.bentcrankshaft.local
    │  Backend returns Ken's Mowers data ✓
    │
    └─ Is it /? → Forward to Next.js frontend (port 3000 inside container)
       Next.js calls: GET /api/v1/site-info
       api.ts passes the slug from domain → ?slug=kens-mowers
       Backend returns Ken's Mowers config ✓
       Next.js renders Ken's Mowers branding ✓
```

---

## 📁 FILES CREATED/MODIFIED

### New Files:
- `docker-compose-test.yml` - Production-identical docker setup (no FFmpeg)
- `nginx_test.conf` - Multi-tenant nginx config for local testing
- `PRODUCTION_IDENTICAL_TEST_SETUP.md` - This file

### Important:
- ✅ NO FFmpeg to avoid resource issues
- ✅ Uses PIL fallback for video thumbnails (fine for testing)
- ✅ nginx handles subdomain routing (just like production)
- ✅ Can safely test features before deploying

---

## 🧹 CLEANUP

### To go back to quick setup:
```bash
docker compose -f docker-compose-test.yml down
docker compose -f docker-compose.quick.yml up -d
```

### To reset database:
```bash
# Backup first!
docker exec db pg_dump > backup.sql

# Then reset
docker compose -f docker-compose-test.yml down -v
docker compose -f docker-compose-test.yml up -d
```

---

## 🔍 TROUBLESHOOTING

### "Connection refused" when accessing bentcrankshaft.local

**Cause:** nginx container not running or not listening

**Fix:**
```bash
docker compose -f docker-compose-test.yml logs nginx
# Check for errors

docker compose -f docker-compose-test.yml restart nginx
```

### "DNS lookup failed"

**Cause:** /etc/hosts entry not added or incorrect

**Fix:**
```bash
# Verify entry exists
cat /etc/hosts | grep bentcrankshaft.local

# Should show:
# 127.0.0.1 bentcrankshaft.local demo.bentcrankshaft.local kens-mowers.bentcrankshaft.local ncpower.bentcrankshaft.local

# Restart DNS (Linux):
sudo systemctl restart systemd-resolved

# Or clear DNS cache (macOS):
sudo dscacheutil -flushcache
```

### "502 Bad Gateway" from nginx

**Cause:** Backend or frontend container not ready

**Fix:**
```bash
# Check if backend is responding
docker compose -f docker-compose-test.yml exec web curl http://localhost:5000/api/v1/site-info

# Check if frontend is running
docker compose -f docker-compose-test.yml logs frontend | tail -20

# Restart nginx
docker compose -f docker-compose-test.yml restart nginx
```

### "Wrong organization showing"

**Cause:** Browser cached old response

**Fix:**
```bash
# Hard refresh browser
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)

# Or clear nginx cache:
docker compose -f docker-compose-test.yml restart nginx
```

---

## ✅ VERIFY PRODUCTION PARITY

After setup, check that you have:

- [x] Database: PostgreSQL at port 5435
- [x] Cache: Redis running
- [x] Backend: Flask API at http://localhost:8005 (internal to containers)
- [x] Frontend: Next.js at http://localhost:3000 (internal to containers)
- [x] Jobs: Worker processing Celery tasks
- [x] Scheduler: Beat handling scheduled posts
- [x] Proxy: nginx routing based on subdomains
- [x] Multi-tenancy: Different orgs show correct branding

**This matches production setup on CT 101!**

---

## 📝 USAGE WORKFLOW

1. **Make code changes on dev branch:**
   ```bash
   git checkout dev
   # Edit files...
   git add -A
   git commit -m "New feature"
   ```

2. **Test thoroughly on CT 106:**
   - Test all three org domains
   - Test admin panel
   - Test media uploads (if changed)
   - Test carousel (if changed)

3. **When confident, merge to main:**
   ```bash
   git checkout main
   git merge dev
   git push origin main
   ```

4. **Deploy to production CT 101:**
   - Follow SAFE_DEPLOYMENT_PLAN.md
   - Pull on CT 101
   - Restart services
   - Verify

---

## 🎯 NOW YOU CAN SAFELY TEST

✅ No more workarounds (preview routes deleted)
✅ No more "Demo Dealer header" issues
✅ No more guessing if features will work in production
✅ Exact production environment to test against
✅ Safe to commit changes knowing they'll work live

**Next step:** Delete preview route since you no longer need it!

---

**Document Version:** 1.0
**Created:** 2026-02-22
**Status:** Ready to implement
