-- Initialize the Civic Sense-Making Platform database
-- This script runs on first database startup

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Set up full text search configuration
CREATE TEXT SEARCH CONFIGURATION IF NOT EXISTS civic_english (COPY=english);

-- Create initial admin user (development only)
-- Password: admin123 (hashed)
-- This will be replaced by proper user creation through the API
