-- Create tables for ported models

CREATE TABLE IF NOT EXISTS dealer (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organization(id),
    name VARCHAR(150) NOT NULL,
    address VARCHAR(300),
    dealer_code VARCHAR(50),
    dealer_dba VARCHAR(150),
    notes TEXT,
    labor_rate VARCHAR(50),
    username VARCHAR(80),
    password VARCHAR(80),
    manufacturers TEXT
);

CREATE TABLE IF NOT EXISTS contact (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organization(id),
    dealer_id INTEGER NOT NULL REFERENCES dealer(id),
    name VARCHAR(100),
    role VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS dealer_note (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organization(id),
    dealer_id INTEGER NOT NULL REFERENCES dealer(id),
    parent_id INTEGER REFERENCES dealer_note(id),
    text TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "user" VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS tag (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organization(id),
    name VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS unit (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organization(id),
    manufacturer VARCHAR(100),
    model_number VARCHAR(100),
    serial_number VARCHAR(100),
    engine_model VARCHAR(100),
    engine_serial VARCHAR(100),
    owner_name VARCHAR(100),
    owner_company VARCHAR(100),
    owner_address VARCHAR(200),
    owner_phone VARCHAR(50),
    owner_email VARCHAR(100),
    unit_hours VARCHAR(50),
    CONSTRAINT _serial_org_uc UNIQUE (serial_number, organization_id)
);

CREATE TABLE IF NOT EXISTS "case" (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organization(id),
    dealer_id INTEGER REFERENCES dealer(id),
    unit_id INTEGER REFERENCES unit(id),
    status VARCHAR(50) DEFAULT 'New',
    case_type VARCHAR(50) NOT NULL DEFAULT 'Support',
    assigned_to VARCHAR(80),
    channel VARCHAR(50),
    reference TEXT,
    is_visit BOOLEAN DEFAULT FALSE,
    creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    appointment_date DATE,
    follow_up_date TIMESTAMP,
    closed_date TIMESTAMP,
    reopened_date TIMESTAMP,
    email_reply_token VARCHAR(100),
    caller_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS case_tags (
    case_id INTEGER REFERENCES "case"(id),
    tag_id INTEGER REFERENCES tag(id),
    PRIMARY KEY (case_id, tag_id)
);

CREATE TABLE IF NOT EXISTS note (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organization(id),
    case_id INTEGER NOT NULL REFERENCES "case"(id),
    parent_id INTEGER REFERENCES note(id),
    text TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "user" VARCHAR(80),
    email_reply_token VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS notification (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organization(id),
    recipient_id INTEGER NOT NULL REFERENCES "user"(id),
    case_id INTEGER REFERENCES "case"(id),
    note_id INTEGER REFERENCES note(id),
    message VARCHAR(255) NOT NULL,
    dealer_note_id INTEGER REFERENCES dealer_note(id),
    is_read BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attachment (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organization(id),
    case_id INTEGER NOT NULL REFERENCES "case"(id),
    filename VARCHAR(200) NOT NULL,
    original_filename VARCHAR(200) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS part_used (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organization(id),
    case_id INTEGER NOT NULL REFERENCES "case"(id),
    part_number VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    cost_at_time_of_use NUMERIC(10, 2) NOT NULL,
    description_at_time_of_use TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS labor_entry (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organization(id),
    case_id INTEGER NOT NULL REFERENCES "case"(id),
    user_id INTEGER NOT NULL REFERENCES "user"(id),
    hours_spent NUMERIC(10, 2) NOT NULL,
    rate_at_time_of_log NUMERIC(10, 2) NOT NULL,
    description TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service Bulletins
CREATE TABLE IF NOT EXISTS service_bulletin (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organization(id),
    sb_number VARCHAR(50) NOT NULL,
    issue_date DATE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    pdf_filename VARCHAR(255),
    pdf_original_name VARCHAR(255),
    warranty_code VARCHAR(50),
    labor_hours VARCHAR(100),
    required_parts TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT _org_sb_uc UNIQUE (organization_id, sb_number)
);

CREATE TABLE IF NOT EXISTS service_bulletin_model (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organization(id),
    bulletin_id INTEGER REFERENCES service_bulletin(id),
    model_name VARCHAR(100) NOT NULL,
    serial_start VARCHAR(50) NOT NULL,
    serial_end VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS service_bulletin_completion (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organization(id),
    bulletin_id INTEGER REFERENCES service_bulletin(id),
    serial_number VARCHAR(50) NOT NULL,
    model_name VARCHAR(100),
    unit_id INTEGER REFERENCES unit(id),
    user_id INTEGER REFERENCES "user"(id),
    completion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    parts_used TEXT DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'Completed'
);
