-- Daily Logger Assist Database Initialization Script
-- This script sets up the basic database structure and permissions

-- Create database if it doesn't exist (handled by PostgreSQL init)
-- CREATE DATABASE IF NOT EXISTS dailylogger;

-- Use the database
\c dailylogger;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create basic user and permissions
-- (The main user is created via environment variables)

-- Create application schema
CREATE SCHEMA IF NOT EXISTS app;

-- Set default privileges for the application user
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT ALL ON TABLES TO dailylogger;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT ALL ON SEQUENCES TO dailylogger;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT ALL ON FUNCTIONS TO dailylogger;

-- Grant usage on schema
GRANT USAGE ON SCHEMA app TO dailylogger;
GRANT CREATE ON SCHEMA app TO dailylogger;

-- Set search path for the user
ALTER USER dailylogger SET search_path TO app, public;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Daily Logger Assist database initialization completed at %', now();
END $$; 