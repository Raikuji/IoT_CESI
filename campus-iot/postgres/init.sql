-- Campus IoT Database Initialization
-- ====================================

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Sensors table
CREATE TABLE IF NOT EXISTS sensors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    location VARCHAR(100) DEFAULT 'C101',
    unit VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sensor data (hypertable for time-series)
CREATE TABLE IF NOT EXISTS sensor_data (
    time TIMESTAMPTZ NOT NULL,
    sensor_id INTEGER REFERENCES sensors(id),
    value DOUBLE PRECISION NOT NULL
);

-- Convert to hypertable (TimescaleDB)
SELECT create_hypertable('sensor_data', 'time', if_not_exists => TRUE);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER REFERENCES sensors(id),
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
    sensor_id INTEGER REFERENCES sensors(id),
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
    location VARCHAR(100) DEFAULT 'C101',
    current_value INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Actuator commands log
CREATE TABLE IF NOT EXISTS actuator_commands (
    id SERIAL PRIMARY KEY,
    actuator_id INTEGER REFERENCES actuators(id),
    command_value INTEGER NOT NULL,
    source VARCHAR(50) DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users table (for auth)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
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

-- Insert default sensors
INSERT INTO sensors (name, type, location, unit) VALUES
    ('BME280 Temperature', 'temperature', 'C101', '°C'),
    ('BME280 Humidity', 'humidity', 'C101', '%'),
    ('BME280 Pressure', 'pressure', 'C101', 'hPa'),
    ('HC-SR04 Presence', 'presence', 'C101 Door', 'bool'),
    ('CO2 Sensor', 'co2', 'C101', 'ppm')
ON CONFLICT DO NOTHING;

-- Insert default actuators
INSERT INTO actuators (name, type, location, current_value) VALUES
    ('Heating Servo', 'servo', 'C101', 0)
ON CONFLICT DO NOTHING;

-- Insert default alert rules
INSERT INTO alert_rules (sensor_id, condition, threshold, message, severity) VALUES
    (1, '>', 28.0, 'Temperature too high', 'warning'),
    (1, '<', 16.0, 'Temperature too low', 'warning'),
    (2, '>', 80.0, 'Humidity too high', 'info'),
    (5, '>', 1000, 'CO2 level high - ventilate', 'danger')
ON CONFLICT DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sensor_data_time ON sensor_data (time DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_data_sensor ON sensor_data (sensor_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_ack ON alerts (is_acknowledged);

-- Default admin user (password: admin123)
INSERT INTO users (username, email, hashed_password, role) VALUES
    ('admin', 'admin@campus.cesi.fr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G8xvGqJ4x8Kqwi', 'admin')
ON CONFLICT DO NOTHING;
