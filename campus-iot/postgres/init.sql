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

-- Alert rules table
CREATE TABLE IF NOT EXISTS alert_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    sensor_id INTEGER REFERENCES sensors(id) ON DELETE CASCADE,
    sensor_type VARCHAR(50),
    room_id VARCHAR(50),
    condition VARCHAR(20) NOT NULL,
    threshold DOUBLE PRECISION NOT NULL,
    message TEXT,
    severity VARCHAR(20) DEFAULT 'warning',
    is_active BOOLEAN DEFAULT true,
    active_days JSONB DEFAULT '[]',
    active_time_start VARCHAR(5),
    active_time_end VARCHAR(5),
    cooldown_minutes INTEGER DEFAULT 5,
    escalation_minutes INTEGER,
    escalation_severity VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER REFERENCES sensors(id) ON DELETE SET NULL,
    rule_id INTEGER REFERENCES alert_rules(id) ON DELETE SET NULL,
    type VARCHAR(50) NOT NULL,
    message TEXT,
    severity VARCHAR(20) DEFAULT 'warning',
    is_acknowledged BOOLEAN DEFAULT false,
    escalation_level INTEGER DEFAULT 0,
    escalated_from_alert_id INTEGER REFERENCES alerts(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ
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

-- Anomalies
CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER REFERENCES sensors(id) ON DELETE SET NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    message TEXT,
    severity VARCHAR(20) DEFAULT 'warning',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit logs (who changed what and when)
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100),
    before_data JSONB,
    after_data JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Webhook endpoints
CREATE TABLE IF NOT EXISTS webhook_endpoints (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret VARCHAR(200),
    event_types JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Export configurations
CREATE TABLE IF NOT EXISTS export_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    resource VARCHAR(50) NOT NULL,
    format VARCHAR(10) DEFAULT 'csv',
    interval_minutes INTEGER DEFAULT 1440,
    time_window_hours INTEGER DEFAULT 24,
    target VARCHAR(20) DEFAULT 'file',
    webhook_id INTEGER REFERENCES webhook_endpoints(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT true,
    last_run_at TIMESTAMPTZ,
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
CREATE INDEX IF NOT EXISTS idx_alerts_rule ON alerts (rule_id);
CREATE INDEX IF NOT EXISTS idx_alert_rules_sensor ON alert_rules (sensor_id);
CREATE INDEX IF NOT EXISTS idx_alert_rules_room ON alert_rules (room_id);
CREATE INDEX IF NOT EXISTS idx_alert_rules_type ON alert_rules (sensor_type);
CREATE INDEX IF NOT EXISTS idx_blockchain_index ON blockchain (block_index);
CREATE INDEX IF NOT EXISTS idx_blockchain_hash ON blockchain (hash);
CREATE INDEX IF NOT EXISTS idx_security_alerts_timestamp ON security_alerts (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_security_alerts_resolved ON security_alerts (resolved);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user ON activity_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_anomalies_sensor ON anomalies (sensor_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_type ON anomalies (anomaly_type);
CREATE INDEX IF NOT EXISTS idx_anomalies_created ON anomalies (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_webhooks_active ON webhook_endpoints (is_active);
CREATE INDEX IF NOT EXISTS idx_exports_active ON export_configs (is_active);
CREATE INDEX IF NOT EXISTS idx_reports_room ON reports (room_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports (status);

-- =============================================
-- PLACED SENSORS (capteurs placés sur le plan)
-- =============================================
CREATE TABLE IF NOT EXISTS placed_sensors (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    position_x DOUBLE PRECISION DEFAULT 0,
    position_y DOUBLE PRECISION DEFAULT 0,
    position_z DOUBLE PRECISION DEFAULT 0,
    name VARCHAR(100),
    current_value DOUBLE PRECISION,
    status VARCHAR(20) DEFAULT 'pending',
    placed_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    placed_by_email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_update TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_placed_sensors_room ON placed_sensors (room_id);
CREATE INDEX IF NOT EXISTS idx_placed_sensors_type ON placed_sensors (sensor_type);

-- =============================================
-- SENSOR ENERGY SETTINGS (par capteur placé)
-- =============================================
CREATE TABLE IF NOT EXISTS sensor_energy_settings (
    id SERIAL PRIMARY KEY,
    placed_sensor_id INTEGER UNIQUE REFERENCES placed_sensors(id) ON DELETE CASCADE,
    energy_enabled BOOLEAN DEFAULT false,
    refresh_interval INTEGER DEFAULT 120,
    refresh_interval_night INTEGER DEFAULT 300,
    disable_live BOOLEAN DEFAULT true,
    profile VARCHAR(20) DEFAULT 'normal',
    schedule_enabled BOOLEAN DEFAULT false,
    schedule_profile VARCHAR(20) DEFAULT 'eco',
    schedule_days JSONB DEFAULT '[]',
    schedule_start VARCHAR(10) DEFAULT '22:00',
    schedule_end VARCHAR(10) DEFAULT '06:00',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sensor_energy_settings_sensor ON sensor_energy_settings (placed_sensor_id);

-- =============================================
-- SYSTEM SETTINGS (paramètres système globaux)
-- =============================================
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    value_type VARCHAR(20) DEFAULT 'string',
    category VARCHAR(50) DEFAULT 'general',
    description TEXT,
    updated_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings (key);
CREATE INDEX IF NOT EXISTS idx_system_settings_category ON system_settings (category);

-- Default system settings
INSERT INTO system_settings (key, value, value_type, category, description) VALUES
    ('temp_min', '18', 'number', 'alerts', 'Température minimum (°C)'),
    ('temp_max', '26', 'number', 'alerts', 'Température maximum (°C)'),
    ('humidity_min', '30', 'number', 'alerts', 'Humidité minimum (%)'),
    ('humidity_max', '70', 'number', 'alerts', 'Humidité maximum (%)'),
    ('co2_max', '1000', 'number', 'alerts', 'CO2 maximum (ppm)'),
    ('presence_timeout', '300', 'number', 'alerts', 'Timeout présence (secondes)'),
    ('anomaly_min_samples', '8', 'number', 'anomalies', 'Échantillons minimum pour détection'),
    ('anomaly_spike_z', '3.0', 'number', 'anomalies', 'Seuil Z-score pour pics'),
    ('anomaly_stuck_window', '10', 'number', 'anomalies', 'Fenêtre détection capteur bloqué'),
    ('anomaly_stuck_epsilon', '0.001', 'number', 'anomalies', 'Tolérance capteur bloqué'),
    ('anomaly_drift_window', '10', 'number', 'anomalies', 'Fenêtre détection dérive'),
    ('anomaly_drift_slope', '0.05', 'number', 'anomalies', 'Seuil pente dérive'),
    ('anomaly_cooldown_minutes', '30', 'number', 'anomalies', 'Cooldown anomalies (minutes)'),
    ('energy_saving_enabled', 'false', 'boolean', 'energy', 'Mode économie d\'énergie'),
    ('energy_saving_refresh_interval', '120', 'number', 'energy', 'Intervalle rafraîchissement eco (secondes)'),
    ('energy_saving_refresh_interval_night', '300', 'number', 'energy', 'Intervalle rafraîchissement nuit (secondes)'),
    ('energy_saving_disable_live', 'true', 'boolean', 'energy', 'Désactiver le temps réel en eco'),
    ('energy_profile', 'normal', 'string', 'energy', 'Profil énergie actif'),
    ('energy_schedule_enabled', 'false', 'boolean', 'energy', 'Planning économie d\'énergie'),
    ('energy_schedule_profile', 'eco', 'string', 'energy', 'Profil planifié (eco/nuit)'),
    ('energy_schedule_days', '[]', 'json', 'energy', 'Jours actifs du planning'),
    ('energy_schedule_start', '22:00', 'string', 'energy', 'Début planning'),
    ('energy_schedule_end', '06:00', 'string', 'energy', 'Fin planning'),
    ('email_notifications', 'true', 'boolean', 'notifications', 'Activer notifications email'),
    ('push_notifications', 'true', 'boolean', 'notifications', 'Activer notifications push'),
    ('default_theme', 'dark', 'string', 'appearance', 'Thème par défaut'),
    ('default_floor', 'RDC', 'string', 'appearance', 'Étage par défaut'),
    ('auto_refresh_interval', '30', 'number', 'general', 'Intervalle rafraîchissement (secondes)'),
    ('data_retention_days', '90', 'number', 'general', 'Rétention données (jours)')
ON CONFLICT (key) DO NOTHING;

-- =============================================
-- USER PREFERENCES (préférences utilisateur)
-- =============================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(20) DEFAULT 'dark',
    default_floor VARCHAR(20) DEFAULT 'RDC',
    notifications_enabled BOOLEAN DEFAULT true,
    email_alerts BOOLEAN DEFAULT false,
    sound_alerts BOOLEAN DEFAULT true,
    dashboard_layout JSONB DEFAULT '{}',
    favorite_rooms JSONB DEFAULT '[]',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences (user_id);

-- Default admin user (password: admin123)
-- Hash generated with bcrypt
INSERT INTO users (email, hashed_password, first_name, last_name, role, department, avatar_color) VALUES
    ('theo.pellizzari@viacesi.fr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G8xvGqJ4x8Kqwi', 'Theo', 'Pellizzari', 'admin', 'Informatique', '#ef4444')
ON CONFLICT (email) DO NOTHING;
