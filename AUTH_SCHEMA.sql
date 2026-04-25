CREATE DATABASE IF NOT EXISTS interview_db;
USE interview_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_salt VARCHAR(32) NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS interviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    user_id VARCHAR(36) NULL,
    topic VARCHAR(100) NOT NULL,
    final_score INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    complete_data JSON NOT NULL,
    INDEX idx_interviews_user_id (user_id),
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
