-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table (if you need to track multiple users)
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Main resumes table
CREATE TABLE resumes (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    full_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    linkedin_url TEXT,
    summary TEXT,
    industry TEXT[],
    file_path TEXT,
    is_valid_resume BOOLEAN DEFAULT TRUE,
    combined_embedding vector(768), -- Adjust dimension based on your embedding model
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skills table
CREATE TABLE resume_skills (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
    skill VARCHAR(255),
    embedding vector(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Experience table
CREATE TABLE resume_experience (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
    title VARCHAR(255),
    company VARCHAR(255),
    description TEXT,
    embedding vector(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Education table
CREATE TABLE resume_education (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
    degree VARCHAR(255),
    institution VARCHAR(255),
    description TEXT,
    embedding vector(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Certifications table
CREATE TABLE resume_certifications (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
    certification VARCHAR(255),
    description TEXT,
    embedding vector(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE resume_projects (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
    name VARCHAR(255),
    description TEXT,
    year VARCHAR(50),
    embedding vector(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_resumes_user_id ON resumes(user_id);
CREATE INDEX idx_resumes_combined_embedding ON resumes USING ivfflat (combined_embedding vector_cosine_ops);
CREATE INDEX idx_skills_resume_id ON resume_skills(resume_id);
CREATE INDEX idx_experience_resume_id ON resume_experience(resume_id);
CREATE INDEX idx_education_resume_id ON resume_education(resume_id);
CREATE INDEX idx_certifications_resume_id ON resume_certifications(resume_id);
CREATE INDEX idx_projects_resume_id ON resume_projects(resume_id);