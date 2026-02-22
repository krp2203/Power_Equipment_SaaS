-- Legacy Schema Creation (Base for Migration)

-- Users
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE,
    password VARCHAR(200) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    cell_phone VARCHAR(50),
    title VARCHAR(100),
    labor_rate NUMERIC(10, 2),
    password_reset_required BOOLEAN DEFAULT FALSE,
    receive_automated_reports BOOLEAN DEFAULT FALSE
);

-- Dealers
CREATE TABLE IF NOT EXISTS dealer (
    id SERIAL PRIMARY KEY,
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

-- Units
CREATE TABLE IF NOT EXISTS unit (
    id SERIAL PRIMARY KEY,
    manufacturer VARCHAR(100),
    model_number VARCHAR(100),
    serial_number VARCHAR(100) UNIQUE,
    engine_model VARCHAR(100),
    engine_serial VARCHAR(100),
    owner_name VARCHAR(100),
    owner_company VARCHAR(100),
    owner_address VARCHAR(200),
    owner_phone VARCHAR(50),
    owner_email VARCHAR(100),
    unit_hours VARCHAR(50)
);

-- Cases
CREATE TABLE IF NOT EXISTS "case" (
    id SERIAL PRIMARY KEY,
    dealer_id INTEGER REFERENCES dealer(id),
    unit_id INTEGER REFERENCES unit(id),
    status VARCHAR(50) DEFAULT 'New',
    case_type VARCHAR(50) DEFAULT 'Support',
    assigned_to VARCHAR(80),
    channel VARCHAR(50),
    reference TEXT,
    is_visit BOOLEAN DEFAULT FALSE,
    creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    appointment_date DATE,
    follow_up_date TIMESTAMP,
    closed_date TIMESTAMP,
    reopened_date TIMESTAMP,
    email_reply_token VARCHAR(100) UNIQUE,
    caller_name VARCHAR(100)
);

-- Service Bulletins
CREATE TABLE IF NOT EXISTS service_bulletin (
    id SERIAL PRIMARY KEY,
    sb_number VARCHAR(50) UNIQUE NOT NULL,
    issue_date DATE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    pdf_filename VARCHAR(255),
    pdf_original_name VARCHAR(255),
    warranty_code VARCHAR(50),
    labor_hours VARCHAR(100),
    required_parts TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Check Sheet Templates
CREATE TABLE IF NOT EXISTS check_sheet_template (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    fields_structure TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Check Sheet Submissions
CREATE TABLE IF NOT EXISTS check_sheet_submission (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES check_sheet_template(id),
    user_id INTEGER REFERENCES "user"(id),
    submitted_data TEXT DEFAULT '{}',
    warranty_notes TEXT DEFAULT '{}',
    parts_data TEXT DEFAULT '[]',
    case_id INTEGER REFERENCES "case"(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Note: Skipping minor join tables for now to minimal viable schema for migration
