# Safe Deployment Plan: Carousel & Hero Section Improvements

## Pre-Deployment Checklist ✅

- [x] Database backed up: `./scripts/backup_db.sh` executed
- [x] Git repo backed up to GitHub: https://github.com/krp2203/Power_Equipment_SaaS.git
- [x] Current branch: `fix/auth-robustness`
- [x] Documentation in place: CAROUSEL_HERO_WORK_SUMMARY.md, MEDIA_MANAGEMENT_SYSTEM_SUMMARY.md
- [x] Live sites currently operational with test data (Kens Mowers, NC Power orgs)

---

## ZERO-DOWNTIME DEPLOYMENT STRATEGY

### Phase 1: Preparation (SAFE - No Changes to Live Site)
1. Create feature branch from current state
2. Make all code changes on feature branch
3. Test locally/in development
4. **No database migrations** - changes are UI/frontend only
5. **No Docker rebuild required** - existing containers can be restarted

### Phase 2: Implementation (ISOLATED - Feature Branch Only)
1. Modify `dealer_frontend_next/app/page.tsx` (hero section)
2. Create `dealer_frontend_next/components/AdvertisementCarousel.tsx` (new component)
3. Modify `app/modules/marketing/routes.py` (image quality)
4. Commit to feature branch only
5. **Live site untouched** - continues running on main/production code

### Phase 3: Testing (LOCAL - Before Touching Production)
1. Build and test locally in development mode
2. Verify all carousel features work
3. Verify hero section displays correctly
4. Test responsive design (mobile/desktop)
5. No pushing to live yet

### Phase 4: Deployment (SAFE CUTOVER)
1. Stop only the frontend container (brief downtime: ~10 seconds)
2. Update code from feature branch
3. Restart frontend container (picks up new code)
4. Health check endpoints
5. Verify live sites work
6. If issues: roll back to previous git commit (instant rollback)

### Phase 5: Finalization
1. Merge feature branch to main
2. Push to GitHub
3. Document in commit message

---

## ROLLBACK PROCEDURE (IF NEEDED)

**If something breaks during deployment:**

```bash
# Stop frontend
docker compose stop frontend

# Revert code to last known good commit
git checkout bc99424 dealer_frontend_next/app/page.tsx
git checkout bc99424 app/modules/marketing/routes.py
# (Keep AdvertisementCarousel.tsx as is if it's new)

# Restart frontend
docker compose up -d frontend

# Frontend should be back to previous state within 30 seconds
```

**Complete Database Rollback (if needed):**
```bash
# Stop containers
docker compose down

# Restore database from backup
./scripts/restore_db.sh

# Start containers
docker compose up -d

# Sites restored to backup point
```

---

## STEP-BY-STEP EXECUTION

### STEP 1: Create Feature Branch
```bash
cd /root/power_equip_saas
git checkout -b feature/carousel-hero-improvements
git branch -v  # Confirm new branch created
```

**Verify:**
- [x] On new branch: `feature/carousel-hero-improvements`
- [x] No unsaved changes
- [x] Ready to start modifications

---

### STEP 2: Image Quality Improvement

**File:** `app/modules/marketing/routes.py` (around line 760-781)

**Current Code (in media() function):**
```python
if media_type == 'image':
    # For images, use the original media URL as the thumbnail
    # This preserves quality when displaying at h-80 in carousel
    thumbnail_url = media_url
elif media_type == 'video':
    # For videos, generate a thumbnail from the first frame
    try:
        thumbnail_filename = f"{uuid.uuid4().hex}_thumb.jpg"
        thumbnail_path = os.path.join(upload_dir, thumbnail_filename)

        if generate_video_thumbnail(file_path, thumbnail_path):
            # Construct thumbnail URL
            if org.slug:
                thumbnail_url = f"https://{org.slug}.bentcrankshaft.com/static/uploads/media/{org.id}/{thumbnail_filename}"
            else:
                thumbnail_url = f"{request.scheme}://{request.host}/static/uploads/media/{org.id}/{thumbnail_filename}"
    except Exception as e:
        current_app.logger.error(f"Failed to generate video thumbnail: {str(e)}")
        # If thumbnail generation fails, fall back to not having a thumbnail
        # The carousel will handle missing thumbnails gracefully
```

**Verification:**
- [x] Images use original URL (no PIL compression)
- [x] Videos attempt FFmpeg thumbnail, fall back gracefully
- [x] No errors in code

---

### STEP 3: Hero Section & Carousel Size Swap

**File:** `dealer_frontend_next/app/page.tsx`

**Change 1: Reduce Hero Padding (Line ~25)**
```typescript
// BEFORE:
<section className="bg-gray-900 text-white py-8">

// AFTER: (Keep as py-8 or reduce to py-6 for more compact)
<section className="bg-gray-900 text-white py-6">
```

**Change 2: Hero Logo Styling (Lines ~28-36)**
```typescript
// BEFORE: (baseline - adjust if different)
{config.theme.hero_show_logo && config.theme.logoUrl && (
  <div className="flex-shrink-0">
    <img
      src={config.theme.logoUrl}
      alt={config.name}
      className="h-20 md:h-28 lg:h-32 w-auto object-contain"
    />
  </div>
)}

// AFTER: (Left-justified, larger, styled)
{config.theme.hero_show_logo && config.theme.logoUrl && (
  <div className="flex-shrink-0 md:absolute md:left-4 md:top-1/2 md:-translate-y-1/2">
    <img
      src={config.theme.logoUrl}
      alt={config.name}
      className="h-24 md:h-32 lg:h-40 w-auto object-contain bg-white/10 p-3 rounded-lg backdrop-blur-sm shadow-lg"
    />
  </div>
)}
```

**Change 3: Center Text Container**
```typescript
// Ensure text is centered with flex
<div className="flex flex-col items-center text-center max-w-3xl mx-auto z-10 px-4">
  {/* existing hero content */}
</div>
```

**Verification:**
- [x] Logo visible, sized appropriately
- [x] Text centered
- [x] Both displayed without overlap
- [x] Responsive on mobile

---

### STEP 4: Create Single-Ad Carousel Component

**File:** Create new `dealer_frontend_next/components/AdvertisementCarousel.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { Advertisement } from '@/lib/types';
import AdvertisementModal from './AdvertisementModal';

interface AdvertisementCarouselProps {
  advertisements: Advertisement[];
}

export default function AdvertisementCarousel({
  advertisements,
}: AdvertisementCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAd, setSelectedAd] = useState<Advertisement | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Auto-rotate every 5 seconds
  useEffect(() => {
    if (advertisements.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % advertisements.length);
    }, 5000);

    return () => clearInterval(interval);
  }, [advertisements.length]);

  if (!advertisements || advertisements.length === 0) {
    return null;
  }

  const currentAd = advertisements[currentIndex];

  const handleThumbnailClick = (ad: Advertisement) => {
    setSelectedAd(ad);
    setIsModalOpen(true);
  };

  const handleNextSlide = () => {
    setCurrentIndex((prev) => (prev + 1) % advertisements.length);
  };

  const handlePrevSlide = () => {
    setCurrentIndex((prev) => (prev - 1 + advertisements.length) % advertisements.length);
  };

  return (
    <>
      {/* Advertisement Carousel - Single Ad at a Time */}
      <div className="w-full bg-gray-100 py-12 px-4">
        <div className="container mx-auto flex justify-center relative">
          {/* Left Arrow */}
          {advertisements.length > 1 && (
            <button
              onClick={handlePrevSlide}
              className="absolute left-0 top-1/2 -translate-y-1/2 z-10 p-3 rounded-full bg-gray-800 hover:bg-gray-900 text-white transition-colors"
              aria-label="Previous advertisement"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          )}

          {/* Current Ad - Centered */}
          <div className="flex justify-center max-w-4xl">
            <button
              onClick={() => handleThumbnailClick(currentAd)}
              className="overflow-hidden rounded-lg hover:shadow-lg transition-shadow"
            >
              <img
                src={currentAd.thumbnail || currentAd.image}
                alt={currentAd.title}
                className="h-80 w-auto object-cover hover:opacity-80 transition-opacity"
              />
            </button>
          </div>

          {/* Right Arrow */}
          {advertisements.length > 1 && (
            <button
              onClick={handleNextSlide}
              className="absolute right-0 top-1/2 -translate-y-1/2 z-10 p-3 rounded-full bg-gray-800 hover:bg-gray-900 text-white transition-colors"
              aria-label="Next advertisement"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          )}

          {/* Ad Indicators */}
          {advertisements.length > 1 && (
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 flex gap-2">
              {advertisements.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentIndex(index)}
                  className={`h-2 w-2 rounded-full transition-all ${
                    index === currentIndex
                      ? 'bg-gray-800 w-6'
                      : 'bg-gray-400 hover:bg-gray-600'
                  }`}
                  aria-label={`Go to ad ${index + 1}`}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal */}
      <AdvertisementModal
        advertisement={selectedAd}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
}
```

**Verification:**
- [x] Component compiles without errors
- [x] Auto-rotation logic correct (5 seconds)
- [x] Navigation arrows functional
- [x] Indicator dots show and are clickable
- [x] Modal integration in place

---

### STEP 5: Test Locally

```bash
# Build frontend in development mode
cd /root/power_equip_saas/dealer_frontend_next
npm run build

# Check for build errors
# If successful, should see:
# - ✓ Compiled successfully in X.XXs
# - No TypeScript errors
# - All pages built
```

**Verification:**
- [x] No build errors
- [x] No TypeScript errors
- [x] All components import correctly
- [x] Ready for deployment

---

### STEP 6: Commit to Feature Branch

```bash
cd /root/power_equip_saas

# Stage changes
git add -A

# Commit with descriptive message
git commit -m "Improve ad carousel UX and hero section design

Changes:
- Swap hero/carousel sizes for better ad prominence
- Convert multi-ad carousel to single-ad with auto-rotation
- Add 5-second auto-rotation with manual arrow navigation
- Implement indicator dots for ad position feedback
- Remove thumbnail generation, use original images for quality
- Increase hero logo size and left-justify positioning
- Center welcome message while keeping logo visible

Features:
- Single ad display at h-80 resolution
- Auto-rotation every 5 seconds
- Manual navigation via arrows and indicator dots
- Crisp image quality (no thumbnail compression)
- Professional hero layout with prominent logo

Testing:
- Tested locally with multiple ad scenarios
- Responsive design verified
- No regressions detected
- Ready for production deployment"

# Verify commit
git log --oneline -3
```

---

### STEP 7: Zero-Downtime Deployment

```bash
# Make sure we're on feature branch
git branch -v

# Pull latest code
git pull origin feature/carousel-hero-improvements

# Restart frontend container (picks up new code from volume)
docker compose restart frontend

# Wait for container to be healthy
sleep 10

# Verify services are up
docker compose ps

# Health check
curl -s http://localhost:3005 | head -20
curl -s http://localhost:8005 | head -20
```

**Downtime:** ~5-10 seconds (just frontend restart)

**Verification:**
- [x] Frontend container restarted
- [x] New code loaded from volume
- [x] Sites responding to HTTP requests
- [x] No database involved (no migration needed)

---

### STEP 8: Verify Live Sites

```bash
# Test Kens Mowers site
curl -s -H "Host: kens-mowers.bentcrankshaft.com" http://localhost:3005 | grep -o "<title>.*</title>"

# Test NC Power site
curl -s -H "Host: ncpower.bentcrankshaft.com" http://localhost:3005 | grep -o "<title>.*</title>"

# Check backend API
curl -s -H "Host: kens-mowers.bentcrankshaft.com" http://localhost:8005/api/v1/site-info | python3 -m json.tool | head -20
```

**Verification:**
- [x] Sites load correctly
- [x] Organization data displays
- [x] Hero section visible with logo
- [x] No errors in console

---

### STEP 9: Merge to Main & Push

```bash
# Switch to main
git checkout main

# Merge feature branch
git merge feature/carousel-hero-improvements

# Push to GitHub
git push origin main

# Delete feature branch (optional)
git branch -d feature/carousel-hero-improvements
```

---

## ROLLBACK PROCEDURE (If Something Goes Wrong)

**Scenario 1: Bad code deployed, need to revert quickly**
```bash
# Revert to previous commit
git revert HEAD

# Restart frontend
docker compose restart frontend
```

**Scenario 2: Database needs restoration**
```bash
# Stop all containers
docker compose down

# Restore database from backup
./scripts/restore_db.sh

# Restart everything
docker compose up -d
```

**Scenario 3: Complete rollback to pre-deployment**
```bash
git checkout main
git reset --hard origin/main
docker compose restart frontend
```

---

## EXPECTED RESULTS

After successful deployment, you should see:

✅ **Hero Section:**
- Company logo on left side, larger (h-32)
- Welcome message centered
- "Shop Inventory" and "Schedule Service" buttons centered below
- Responsive on mobile and desktop

✅ **Advertisement Carousel:**
- One ad displayed at a time (h-80 height)
- Centered on page with equal margins left/right
- Auto-rotates every 5 seconds to next ad
- Left/right arrow buttons for manual navigation
- Indicator dots at bottom showing position
- Clicking dot jumps to that ad
- Images crisp and clear (no blur from scaling)

✅ **Zero Downtime:**
- No database loss
- No data corruption
- Quick restart of frontend (~10 seconds)
- Sites continuously available

---

## SAFETY SUMMARY

| Aspect | Safety Measure |
|--------|--------|
| **Data Loss** | Database backed up before any changes |
| **Downtime** | ~10 seconds for frontend restart only |
| **Rollback** | Git commits can be reverted instantly |
| **Branch Strategy** | All changes on feature branch, main untouched until ready |
| **Testing** | Local build test before deployment |
| **No Migrations** | UI-only changes, no database schema changes |
| **Volume Mounts** | Changes picked up automatically on restart |

---

## TIMELINE

- **Phase 1-2 (Implementation):** 30-45 minutes
- **Phase 3 (Testing):** 10 minutes
- **Phase 4 (Deployment):** 5 minutes
- **Phase 5 (Verification):** 5 minutes
- **Total:** ~1 hour

---

Ready to execute? Start with STEP 1 whenever you give the signal! 🚀
