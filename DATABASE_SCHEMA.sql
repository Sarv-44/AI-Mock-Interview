-- DATABASE_SCHEMA.sql
-- Consolidated schema snapshot for the interview prep app.
-- This file replaces the older split schema snapshots.
--
-- Source of truth:
-- backend/database.py:init_database()
--
-- Notes:
-- - This file captures the current runtime table shape.
-- - Catalog and study-material seed data are populated by app startup.

CREATE DATABASE IF NOT EXISTS interview_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE interview_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    password_salt VARCHAR(32) NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS topics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(100) NOT NULL,
    title VARCHAR(150) NOT NULL,
    subtitle VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    level_label VARCHAR(100) NOT NULL,
    accent VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    question_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_id VARCHAR(100) UNIQUE NOT NULL,
    topic_id VARCHAR(100) NOT NULL,
    question_text TEXT NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    display_order INT NOT NULL,
    sample_answer TEXT NULL,
    ideal_answer TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_questions_topic_id (topic_id),
    INDEX idx_questions_difficulty (difficulty),
    CONSTRAINT fk_questions_topic_id
        FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS job_roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(150) NOT NULL,
    subtitle VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    level_label VARCHAR(100) NOT NULL,
    default_duration INT NOT NULL DEFAULT 30,
    available_durations JSON NOT NULL,
    topic_weights JSON NOT NULL,
    primary_topic_id VARCHAR(100) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS interviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    user_id VARCHAR(36) NULL,
    topic VARCHAR(100) NOT NULL,
    session_mode VARCHAR(20) NOT NULL DEFAULT 'topic',
    role_id VARCHAR(100) NULL,
    final_score INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    complete_data JSON NOT NULL,
    INDEX idx_interviews_user_id (user_id),
    INDEX idx_interviews_role_id (role_id),
    CONSTRAINT fk_interviews_user_id
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS topic_ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    user_id VARCHAR(36) NULL,
    topic_id VARCHAR(100) NOT NULL,
    rating TINYINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_topic_ratings_topic_id (topic_id),
    INDEX idx_topic_ratings_user_id (user_id),
    CONSTRAINT fk_topic_ratings_session_id
        FOREIGN KEY (session_id) REFERENCES interviews(session_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_topic_ratings_user_id
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS topic_activity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    topic_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_topic_activity_topic_id (topic_id),
    INDEX idx_topic_activity_user_id (user_id),
    CONSTRAINT fk_topic_activity_session_id
        FOREIGN KEY (session_id) REFERENCES interviews(session_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_topic_activity_user_id
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS custom_interviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id VARCHAR(64) UNIQUE NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    title VARCHAR(160) NOT NULL,
    description TEXT NULL,
    total_duration_minutes INT NOT NULL DEFAULT 30,
    questions_json LONGTEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_custom_interviews_user_id (user_id),
    CONSTRAINT fk_custom_interviews_user_id
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS topic_study_materials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id VARCHAR(100) UNIQUE NOT NULL,
    topic_title VARCHAR(150) NOT NULL,
    overview TEXT NOT NULL,
    revision_notes TEXT NOT NULL,
    common_mistakes TEXT NULL,
    rapid_fire_points JSON NOT NULL,
    practice_prompts JSON NOT NULL,
    estimated_minutes INT NOT NULL DEFAULT 20,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_topic_study_materials_topic_id
        FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS study_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plan_id VARCHAR(64) UNIQUE NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    role_id VARCHAR(100) NOT NULL,
    role_title VARCHAR(150) NOT NULL,
    title VARCHAR(180) NOT NULL,
    target_days INT NOT NULL DEFAULT 40,
    focus_topic_ids JSON NOT NULL,
    role_snapshot JSON NOT NULL,
    plan_summary JSON NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_study_plans_user_id (user_id),
    INDEX idx_study_plans_role_id (role_id),
    CONSTRAINT fk_study_plans_user_id
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS study_plan_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    step_id VARCHAR(64) UNIQUE NOT NULL,
    plan_id VARCHAR(64) NOT NULL,
    sequence_no INT NOT NULL,
    phase_key VARCHAR(30) NOT NULL,
    step_type VARCHAR(30) NOT NULL,
    scheduled_day INT NOT NULL,
    scheduled_label VARCHAR(80) NOT NULL,
    topic_id VARCHAR(100) NULL,
    topic_title VARCHAR(150) NULL,
    role_id VARCHAR(100) NULL,
    role_title VARCHAR(150) NULL,
    question_ids JSON NULL,
    snapshot_json JSON NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'planned',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_study_plan_steps_plan_id (plan_id),
    INDEX idx_study_plan_steps_day (scheduled_day),
    INDEX idx_study_plan_steps_status (status),
    CONSTRAINT fk_study_plan_steps_plan_id
        FOREIGN KEY (plan_id) REFERENCES study_plans(plan_id)
        ON DELETE CASCADE
);
