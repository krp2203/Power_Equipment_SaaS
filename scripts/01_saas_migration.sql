-- Transaction Start
BEGIN;

-- 1. Create Organization Table
CREATE TABLE IF NOT EXISTS organization (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Insert Master Organization
INSERT INTO organization (id, name, settings)
VALUES (1, 'Master Organization', '{"active_plugins": [], "is_master": true}')
ON CONFLICT (id) DO NOTHING;

-- Reset sequence to avoid id 1 collision for new orgs
SELECT setval('organization_id_seq', (SELECT MAX(id) FROM organization));

-- Helper macro/function for adding org_id safely
-- (Writing out explicitly for clarity and compatibility)

-- 3. Migrate USERS
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS organization_id INTEGER DEFAULT 1;
ALTER TABLE "user" ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE "user" ALTER COLUMN organization_id DROP DEFAULT; -- remove default after population
ALTER TABLE "user" ADD CONSTRAINT fk_user_organization FOREIGN KEY (organization_id) REFERENCES organization(id);

-- 4. Migrate DEALERS
ALTER TABLE dealer ADD COLUMN IF NOT EXISTS organization_id INTEGER DEFAULT 1;
ALTER TABLE dealer ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE dealer ALTER COLUMN organization_id DROP DEFAULT;
ALTER TABLE dealer ADD CONSTRAINT fk_dealer_organization FOREIGN KEY (organization_id) REFERENCES organization(id);

-- 5. Migrate CASES
ALTER TABLE "case" ADD COLUMN IF NOT EXISTS organization_id INTEGER DEFAULT 1;
ALTER TABLE "case" ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE "case" ALTER COLUMN organization_id DROP DEFAULT;
ALTER TABLE "case" ADD CONSTRAINT fk_case_organization FOREIGN KEY (organization_id) REFERENCES organization(id);

-- 6. Migrate UNITS
ALTER TABLE unit ADD COLUMN IF NOT EXISTS organization_id INTEGER DEFAULT 1;
ALTER TABLE unit ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE unit ALTER COLUMN organization_id DROP DEFAULT;
ALTER TABLE unit ADD CONSTRAINT fk_unit_organization FOREIGN KEY (organization_id) REFERENCES organization(id);

-- 7. Migrate SERVICE BULLETINS
ALTER TABLE service_bulletin ADD COLUMN IF NOT EXISTS organization_id INTEGER DEFAULT 1;
ALTER TABLE service_bulletin ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE service_bulletin ALTER COLUMN organization_id DROP DEFAULT;
ALTER TABLE service_bulletin ADD CONSTRAINT fk_sb_organization FOREIGN KEY (organization_id) REFERENCES organization(id);

-- 8. Migrate CHECK SHEET TEMPLATES
ALTER TABLE check_sheet_template ADD COLUMN IF NOT EXISTS organization_id INTEGER DEFAULT 1;
ALTER TABLE check_sheet_template ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE check_sheet_template ALTER COLUMN organization_id DROP DEFAULT;
ALTER TABLE check_sheet_template ADD CONSTRAINT fk_cst_organization FOREIGN KEY (organization_id) REFERENCES organization(id);

-- 9. Migrate CHECK SHEET SUBMISSIONS
ALTER TABLE check_sheet_submission ADD COLUMN IF NOT EXISTS organization_id INTEGER DEFAULT 1;
ALTER TABLE check_sheet_submission ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE check_sheet_submission ALTER COLUMN organization_id DROP DEFAULT;
ALTER TABLE check_sheet_submission ADD CONSTRAINT fk_css_organization FOREIGN KEY (organization_id) REFERENCES organization(id);

-- Add typical composite constraints for uniqueness where applicable
-- Example: Serial numbers are now unique PER ORG, not globally.
-- Note: This requires dropping existing unique constraints first if they exist.
-- ALTER TABLE unit DROP CONSTRAINT IF EXISTS unit_serial_number_key;
-- ALTER TABLE unit ADD CONSTRAINT unit_serial_number_org_key UNIQUE (serial_number, organization_id);

COMMIT;
