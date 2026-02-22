#!/usr/bin/env python3
"""
Safe deletion script for test dealers.
Deletes all related records cascade-style to avoid foreign key constraint violations.
"""

import sys
sys.path.insert(0, '/root/power_equip_saas')

from app import create_app
from app.core.models import (
    Organization, User, Dealer, Contact, DealerNote, Tag,
    Unit, UnitImage, Case, Note, Notification, Attachment,
    PartUsed, LaborEntry, AuditLog, PartInventory, FacebookPost,
    ServiceBulletin, ServiceBulletinModel, ServiceBulletinCompletion
)
from app.core.extensions import db

app = create_app()

def delete_organization_cascade(org_id, org_name):
    """Safely delete an organization and all its related records."""
    try:
        with app.app_context():
            org = Organization.query.get(org_id)
            if not org:
                print(f"❌ Organization with ID {org_id} not found")
                return False

            print(f"\n{'='*60}")
            print(f"Deleting: {org_name} (ID: {org_id})")
            print(f"{'='*60}")

            # Delete in order of dependencies (child tables first)

            # 1. Delete ServiceBulletinCompletions (depends on ServiceBulletinModel)
            sb_completions = ServiceBulletinCompletion.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(sb_completions)} service bulletin completions...")
            for item in sb_completions:
                db.session.delete(item)

            # 2. Delete ServiceBulletinModels (depends on ServiceBulletin)
            sb_models = ServiceBulletinModel.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(sb_models)} service bulletin models...")
            for item in sb_models:
                db.session.delete(item)

            # 3. Delete ServiceBulletins
            bulletins = ServiceBulletin.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(bulletins)} service bulletins...")
            for bulletin in bulletins:
                db.session.delete(bulletin)

            # 4. Delete FacebookPosts
            fb_posts = FacebookPost.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(fb_posts)} Facebook posts...")
            for post in fb_posts:
                db.session.delete(post)

            # 5. Delete LaborEntries and PartUsed (depends on Case)
            labor_entries = LaborEntry.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(labor_entries)} labor entries...")
            for entry in labor_entries:
                db.session.delete(entry)

            parts_used = PartUsed.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(parts_used)} parts used...")
            for part in parts_used:
                db.session.delete(part)

            # 6. Delete Attachments and Notes (depends on Case)
            attachments = Attachment.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(attachments)} attachments...")
            for attachment in attachments:
                db.session.delete(attachment)

            notes = Note.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(notes)} notes...")
            for note in notes:
                db.session.delete(note)

            # 7. Delete Cases
            cases = Case.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(cases)} cases...")
            for case in cases:
                db.session.delete(case)

            # 8. Delete Notifications
            notifications = Notification.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(notifications)} notifications...")
            for notif in notifications:
                db.session.delete(notif)

            # 9. Delete AuditLogs
            audit_logs = AuditLog.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(audit_logs)} audit logs...")
            for log in audit_logs:
                db.session.delete(log)

            # 10. Delete Units (UnitImages will be deleted with cascade)
            units = Unit.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(units)} units (and their images)...")
            for unit in units:
                # Delete images for this unit
                images = UnitImage.query.filter_by(unit_id=unit.id).all()
                for image in images:
                    db.session.delete(image)
                # Delete unit
                db.session.delete(unit)

            # 12. Delete PartInventory
            parts = PartInventory.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(parts)} parts...")
            for part in parts:
                db.session.delete(part)

            # 13. Delete DealerNotes
            dealer_notes = DealerNote.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(dealer_notes)} dealer notes...")
            for note in dealer_notes:
                db.session.delete(note)

            # 14. Delete Contacts
            contacts = Contact.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(contacts)} contacts...")
            for contact in contacts:
                db.session.delete(contact)

            # 15. Delete Dealers
            dealers = Dealer.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(dealers)} dealers...")
            for dealer in dealers:
                db.session.delete(dealer)

            # 16. Delete Users (depends on Organization)
            users = User.query.filter_by(organization_id=org_id).all()
            print(f"  - Deleting {len(users)} users...")
            for user in users:
                db.session.delete(user)

            # 10. Finally, delete the Organization
            print(f"  - Deleting organization record...")
            db.session.delete(org)

            # Commit everything
            db.session.commit()
            print(f"\n✅ Successfully deleted {org_name} and all related records!")
            return True

    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error deleting {org_name}: {str(e)}")
        return False

def main():
    """Main function to delete test dealers."""
    with app.app_context():
        # Get all organizations to find the test ones
        all_orgs = Organization.query.all()

        print("\n" + "="*60)
        print("EXISTING ORGANIZATIONS")
        print("="*60)
        for org in all_orgs:
            print(f"  ID: {org.id:3d} | Name: {org.name:30s} | Slug: {org.slug}")

        # Find and delete test dealers
        test_dealers = [
            ("Bob's Mower", "bobs-mower"),
            ("Bypass 1771176967", "bypass-1771176967")
        ]

        deleted_count = 0
        for dealer_name, expected_slug in test_dealers:
            org = Organization.query.filter_by(name=dealer_name).first()
            if org:
                if delete_organization_cascade(org.id, dealer_name):
                    deleted_count += 1
            else:
                # Try by slug
                org = Organization.query.filter_by(slug=expected_slug).first()
                if org:
                    if delete_organization_cascade(org.id, org.name):
                        deleted_count += 1
                else:
                    print(f"\n⚠️  Could not find dealer: {dealer_name}")

        print(f"\n{'='*60}")
        print(f"DELETION SUMMARY: {deleted_count} dealer(s) deleted successfully")
        print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
