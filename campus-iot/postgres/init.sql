-- Campus IoT Database Initialization
-- ====================================
-- Compatible with Supabase (standard PostgreSQL, no TimescaleDB)

-- Sensors table
CREATE TABLE IF NOT EXISTS sensors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    location VARCHAR(100),
    room_id VARCHAR(50),
    unit VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sensor data (standard table for time-series)
CREATE TABLE IF NOT EXISTS sensor_data (
    id SERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sensor_id INTEGER REFERENCES sensors(id) ON DELETE CASCADE,
    value DOUBLE PRECISION NOT NULL
);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER REFERENCES sensors(id) ON DELETE SET NULL,
    type VARCHAR(50) NOT NULL,
    message TEXT,
    severity VARCHAR(20) DEFAULT 'warning',
    is_acknowledged BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ
);

-- Alert rules table
CREATE TABLE IF NOT EXISTS alert_rules (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER REFERENCES sensors(id) ON DELETE CASCADE,
    condition VARCHAR(20) NOT NULL,
    threshold DOUBLE PRECISION NOT NULL,
    message TEXT,
    severity VARCHAR(20) DEFAULT 'warning',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Actuators table
CREATE TABLE IF NOT EXISTS actuators (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    location VARCHAR(100),
    room_id VARCHAR(50),
    current_value INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Actuator commands log
CREATE TABLE IF NOT EXISTS actuator_commands (
    id SERIAL PRIMARY KEY,
    actuator_id INTEGER REFERENCES actuators(id) ON DELETE CASCADE,
    command_value INTEGER NOT NULL,
    source VARCHAR(50) DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users table (for authentication)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    department VARCHAR(100) DEFAULT 'CESI Nancy',
    avatar_color VARCHAR(20) DEFAULT '#3b82f6',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- Activity logs
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- System logs
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL,
    source VARCHAR(50),
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Blockchain table (for data integrity)
CREATE TABLE IF NOT EXISTS blockchain (
    id SERIAL PRIMARY KEY,
    block_index INTEGER UNIQUE NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    sensor_type VARCHAR(50),
    sensor_value VARCHAR(100),
    data_hash VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    hash VARCHAR(64) UNIQUE NOT NULL,
    nonce INTEGER DEFAULT 0,
    signature_valid BOOLEAN DEFAULT true,
    source_ip VARCHAR(45)
);

-- Security alerts table
CREATE TABLE IF NOT EXISTS security_alerts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'warning',
    description TEXT,
    raw_data TEXT,
    source_ip VARCHAR(45),
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMPTZ,
    resolved_by VARCHAR(100)
);

-- Reports table (for QR code issue reporting)
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(50) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    description TEXT,
    reported_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reported_by_email VARCHAR(255),
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    resolved_by_email VARCHAR(255)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sensor_data_time ON sensor_data (time DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_data_sensor ON sensor_data (sensor_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_ack ON alerts (is_acknowledged);
CREATE INDEX IF NOT EXISTS idx_blockchain_index ON blockchain (block_index);
CREATE INDEX IF NOT EXISTS idx_blockchain_hash ON blockchain (hash);
CREATE INDEX IF NOT EXISTS idx_security_alerts_timestamp ON security_alerts (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_security_alerts_resolved ON security_alerts (resolved);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user ON activity_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_room ON reports (room_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports (status);

-- Default admin user (password: admin123)
-- Hash generated with bcrypt
INSERT INTO users (email, hashed_password, first_name, last_name, role, department, avatar_color) VALUES
    ('theo.pellizzari@viacesi.fr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G8xvGqJ4x8Kqwi', 'Theo', 'Pellizzari', 'admin', 'Informatique', '#ef4444')
ON CONFLICT (email) DO NOTHING;
