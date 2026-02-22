# Universal Marketing/Media Management System - Work Summary

This document details the media management system created in commit `ec67d40` (now reverted). This work can be restored once production database is recovered.

---

## OVERVIEW

A comprehensive **unified media management system** was created to allow dealers to:
- Upload images and videos once
- Schedule when they appear
- Post to multiple destinations simultaneously (Facebook, Instagram, Website Banner)
- Track posting history and status
- Manage promotional content centrally

---

## SYSTEM ARCHITECTURE

### Models Created
**File:** `app/core/models.py`

**New Models Added:**
1. **MediaContent** - Central media record
   - `id`: Primary key
   - `organization_id`: Multi-tenancy
   - `title`: Media title
   - `description`: Longer description for social media
   - `media_url`: URL to uploaded file (image or video)
   - `thumbnail_url`: Auto-generated thumbnail
   - `media_type`: 'image' or 'video'
   - `link_url`: Optional click-through URL
   - `post_to_facebook`: Boolean
   - `post_to_instagram`: Boolean
   - `post_to_banner`: Boolean
   - `scheduled_post_time`: When to post (for future scheduling)
   - `status`: 'draft', 'posted', 'scheduled', 'archived'
   - `created_at`, `updated_at`: Timestamps

2. **ScheduledPost** - Tracks scheduled/posted items
   - `id`: Primary key
   - `organization_id`: Multi-tenancy
   - `media_content_id`: Links to MediaContent
   - `destination`: 'facebook', 'instagram', 'banner'
   - `scheduled_time`: When to post
   - `status`: 'pending', 'posted', 'failed'
   - `created_at`, `updated_at`: Timestamps

3. **Banner** - Website banner management
   - `id`: Primary key
   - `organization_id`: Multi-tenancy
   - `image_url`: Full-size image URL
   - `thumbnail_url`: Small preview
   - `title`: Banner title
   - `link_url`: Click destination
   - `sort_order`: Display order
   - `start_date`, `end_date`: Active period
   - `is_active`: Boolean
   - `created_at`: Timestamp

---

## API ENDPOINTS & ROUTES

**File:** `app/modules/marketing/routes.py`

### New Endpoints Created:

#### 1. `/marketing/media` - GET/POST
- **GET**: Display media management page with upload form and library
- **POST**: Handle single file upload, create MediaContent record
- Returns form and list of previous uploads

#### 2. `/marketing/media/<id>/get` - GET
- Get details of a specific media item (AJAX)
- Returns: id, title, description, link_url, post_to_facebook, post_to_instagram, post_to_banner, status

#### 3. `/marketing/media/<id>/update` - POST
- Update media details (title, description, link, destinations)
- Regenerates video thumbnail if title changed

#### 4. `/marketing/media/<id>/delete` - POST
- Delete a media item
- Returns success message

#### 5. `/marketing/media/<id>/refresh` - POST
- Check status of media item (especially pending FB/IG posts)
- Returns current status as JSON

#### 6. `/marketing/banners` - GET/POST
- **GET**: Display banner management page
- **POST**: Upload new banner image

#### 7. `/marketing/banners/reorder` - POST
- Update sort order of banners (AJAX)
- Accepts JSON array of banner IDs in new order

#### 8. `/marketing/banners/<id>/update` - POST
- Update banner details (title, link, dates, active status)

#### 9. `/marketing/banners/<id>/delete` - POST
- Delete a banner

#### 10. `/marketing/complete-chunk-upload` - POST
- Finalize chunked upload for large video files
- Creates MediaContent record
- Generates video thumbnail
- Posts to destinations if selected

### Support Functions:

**generate_video_thumbnail()** - Lines 17-47
```python
def generate_video_thumbnail(video_path, output_path, timestamp='00:00:01'):
    """Extract frame from video at timestamp"""
    # Uses FFmpeg to extract 1-second mark
    # Outputs 400x300 JPEG at quality 5
    # Returns True if successful
```

**regenerate_video_thumbnail()** - Lines 851-962
```python
def regenerate_video_thumbnail(title, org_id, thumbnail_url):
    """Regenerate thumbnail with new title overlay"""
    # Creates PIL image with play button and title text
    # Split design: dark top (play button) + white bottom (text)
    # Returns updated thumbnail URL
```

---

## TEMPLATES CREATED

### 1. `app/modules/marketing/templates/marketing/media.html`

**Main Features:**
- **Upload Form Section**
  - Title input (internal name)
  - Description textarea (for social media)
  - Link URL input (optional click destination)
  - File upload with drag-and-drop
  - File preview (image or video)
  - File size and type validation

- **Destination Selection**
  - Checkbox for Facebook (disabled if not configured)
  - Checkbox for Instagram (disabled if not configured)
  - Checkbox for Website Banner
  - Status badges showing configuration status

- **Scheduling Options**
  - Radio buttons: "Post Now" or "Schedule for Later"
  - Date picker for scheduled date
  - Time picker for scheduled time
  - Timezone handling

- **Media Library/History**
  - Table of previously uploaded media
  - Shows: Thumbnail, Title, Type, Destinations, Status, Date
  - Edit button (opens modal for updating)
  - Delete button with confirmation
  - Refresh button (check status of pending posts)
  - Status badges (Draft, Posted, Scheduled, Archived)

**Form Validation:**
- File type validation (image/video)
- At least one destination must be selected
- Date/time validation for scheduling

### 2. `app/modules/marketing/templates/marketing/banners.html`

**Features:**
- Upload banner image form
- Drag-and-drop file upload
- Banner title and link URL
- Date range selection (start/end dates)
- Banner management table:
  - Preview thumbnail
  - Title
  - Link URL
  - Active dates
  - Active/Inactive toggle
  - Edit button
  - Delete button
- Drag-to-reorder functionality for sort order
- Date range display (e.g., "Jan 15 - Feb 28")

### 3. `app/modules/marketing/templates/marketing/history.html`

**Features:**
- Post history viewer
- Sorted by date (most recent first)
- Shows: Type (Photo/Video/Text), Title, Message, Status
- Facebook Post ID (if posted)
- Instagram crosspost indicator
- Date/time posted
- Optional status update

---

## BACKEND FORMS

**File:** `app/modules/marketing/forms.py`

### Forms Created:

**MediaUploadForm**
- Media file field (image or video)
- Title field (required)
- Description field (optional)
- Link URL field (optional)
- Post to Facebook checkbox
- Post to Instagram checkbox
- Post to Banner checkbox
- Schedule mode selection (now/scheduled)
- Scheduled date/time fields

---

## CELERY TASKS

**File:** `app/tasks/marketing.py`

### Tasks Created:

**post_media_task(org_id, message, media_url, title, media_content_id, post_to_instagram, media_type)**
- Async task for posting media to Facebook/Instagram
- Called when media is uploaded with social destinations selected
- Handles both images and videos
- Updates MediaContent status when complete
- Error handling and retry logic

---

## FILE UPLOAD SYSTEM

**File:** `app/modules/marketing/chunk_upload.py`

**Features:**
- Chunked upload for large files
- Resumable uploads (user can retry failed chunks)
- File assembly after all chunks received
- Temporary chunk storage
- Cleanup of temp files after assembly

**Endpoints:**
- `/marketing/init-chunk-upload` - Initialize upload session
- `/marketing/upload-chunk` - Upload individual chunk
- `/marketing/complete-chunk-upload` - Finalize and create records

**Flow:**
1. Frontend initiates upload (gets upload ID)
2. Sends file in chunks (5MB each typically)
3. Server stores chunks temporarily
4. When all chunks received, assembles them
5. Creates final file in uploads directory
6. Creates MediaContent and ScheduledPost records
7. Cleans up temporary chunk files

---

## THUMBNAIL GENERATION

### Image Thumbnails
- Original image used directly (no compression)
- Preserves quality when scaled up
- Saves storage space

### Video Thumbnails
- **Method 1: FFmpeg (if available)**
  - Extracts frame at 1 second mark
  - Outputs 400x300 JPEG, quality 5
  - 30-second timeout per video

- **Method 2: PIL Placeholder (fallback)**
  - Creates professional placeholder image
  - Design: Dark top half + white bottom half
  - Red play button circle with white triangle
  - Text overlay with video title
  - Sized to 300x200px

**Regeneration:**
- When media title changes, video thumbnail regenerated
- Allows dealers to update title without re-uploading video
- Uses regenerate_video_thumbnail() function

---

## MULTI-DESTINATION POSTING

### Facebook Integration
- Posts to Facebook page (if configured)
- Supports both images and videos
- Message includes title + description
- Can crosspost to Instagram from Facebook page

### Instagram Integration
- Posts to Instagram business account (if linked to Facebook)
- Works via Facebook Graph API
- Requires proper Instagram business setup

### Website Banner
- Displays on homepage carousel
- Can schedule start/end dates
- Multiple banners shown in order
- Supports active/inactive toggle

---

## SCHEDULING SYSTEM

### Immediate Posting
- Selected when "Post Now" chosen
- Creates ScheduledPost record with current time
- Task queued immediately via Celery

### Delayed Posting
- Selected when "Schedule for Later" chosen
- User picks future date and time
- ScheduledPost record created with scheduled_time
- Status set to 'pending'
- Requires Celery Beat scheduler to check and post at time

### Status Tracking
- 'draft': Saved but not posted
- 'scheduled': Waiting for scheduled time
- 'posted': Successfully posted
- 'failed': Error during posting
- 'archived': Old posts (for cleanup)

---

## REDO CHECKLIST

### Phase 1: Models & Database
- [ ] Add `MediaContent` model to `app/core/models.py`
- [ ] Add `ScheduledPost` model to `app/core/models.py`
- [ ] Add `Banner` model to `app/core/models.py`
- [ ] Run database migrations: `flask db upgrade`

### Phase 2: Forms
- [ ] Create `app/modules/marketing/forms.py`
- [ ] Add `MediaUploadForm` class
- [ ] Add validation for file types
- [ ] Add validation for destination selection

### Phase 3: Templates
- [ ] Create `app/modules/marketing/templates/marketing/media.html`
- [ ] Create `app/modules/marketing/templates/marketing/banners.html`
- [ ] Create `app/modules/marketing/templates/marketing/history.html`
- [ ] Add upload form with drag-and-drop
- [ ] Add media library display
- [ ] Add scheduling form

### Phase 4: Routes
- [ ] Add media upload route (GET/POST)
- [ ] Add media get/update/delete routes
- [ ] Add banner CRUD routes
- [ ] Add complete-chunk-upload route
- [ ] Implement thumbnail generation
- [ ] Add regenerate_video_thumbnail function

### Phase 5: Celery Tasks
- [ ] Create `app/tasks/marketing.py`
- [ ] Add `post_media_task` for async posting
- [ ] Add Facebook posting logic
- [ ] Add Instagram posting logic
- [ ] Add error handling and retries

### Phase 6: Chunked Upload
- [ ] Ensure `app/modules/marketing/chunk_upload.py` exists
- [ ] Implement chunk upload endpoints
- [ ] Implement chunk assembly
- [ ] Test with large files

### Phase 7: Testing
- [ ] Upload image and verify display
- [ ] Upload video and verify thumbnail generation
- [ ] Test Facebook posting (if configured)
- [ ] Test scheduling
- [ ] Test banner display
- [ ] Test file deletion

---

## KEY FILES TO RECREATE

1. **Models:** `app/core/models.py`
   - MediaContent class
   - ScheduledPost class
   - Banner class

2. **Templates:** `app/modules/marketing/templates/marketing/`
   - `media.html` (main upload & management page)
   - `banners.html` (banner management)
   - `history.html` (posting history)

3. **Routes:** `app/modules/marketing/routes.py`
   - Media endpoints
   - Banner endpoints
   - Thumbnail generation
   - File upload handling

4. **Forms:** `app/modules/marketing/forms.py`
   - MediaUploadForm

5. **Tasks:** `app/tasks/marketing.py`
   - post_media_task
   - Scheduling logic

6. **Uploads:** `app/modules/marketing/chunk_upload.py`
   - Chunked upload implementation

---

## NOTES FOR RESTORATION

- **Database models must be created first** - forms and routes depend on them
- **FFmpeg is optional** - system has PIL fallback for video thumbnails
- **Celery Beat must be running** for scheduled posts to post automatically
- **Facebook/Instagram configuration** required in settings for social posting
- **Test media upload with both images and videos** to verify thumbnail generation
- **Chunked upload is for large files** - regular upload works for smaller files

---

## COMMIT MESSAGE

```
Add comprehensive unified media management system

Features:
- Single upload interface for images and videos
- Multi-destination posting (Facebook, Instagram, Website Banner)
- Scheduling support for future posts
- Automatic thumbnail generation (FFmpeg for video, PIL fallback)
- Chunked upload for large files
- Media library with edit/delete functionality
- Banner management with date ranges and sort order
- Post history tracking and status monitoring
- Drag-and-drop file upload
- File preview before upload

New Models:
- MediaContent: Central media record with multi-destination support
- ScheduledPost: Tracks scheduled and posted items
- Banner: Website banner management

New Endpoints:
- /marketing/media - Main media management page
- /marketing/media/<id>/update - Update media details
- /marketing/media/<id>/delete - Delete media
- /marketing/banners - Banner management
- /marketing/complete-chunk-upload - Finalize large uploads

Files Created:
- app/modules/marketing/templates/marketing/media.html
- app/modules/marketing/templates/marketing/banners.html
- app/modules/marketing/templates/marketing/history.html
- app/tasks/marketing.py

Supports:
- Post to multiple destinations simultaneously
- Schedule posts for future dates/times
- Auto-generate video thumbnails with play button
- Drag-and-drop upload interface
- File preview before upload
- Multi-tenancy via organization_id
```

---

## INTEGRATION WITH ADVERTISEMENT CAROUSEL

This media management system feeds content to the **AdvertisementCarousel** component:
- Media uploaded here appears as advertisements on homepage
- Auto-rotation every 5 seconds
- Manual navigation via arrows
- Indicator dots show position
- Clicking ad can open link (if configured)

See `CAROUSEL_HERO_WORK_SUMMARY.md` for carousel implementation details.
