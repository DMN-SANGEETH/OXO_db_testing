import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        database="resume_db",
        user="dmns",
        password="dmns",
        port=5432
    )

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            )
        """)
        extension_exists = cursor.fetchone()[0]
        if not extension_exists:
            print("Vector extension not found. Attempting to create...")
            try:
                cursor.execute("CREATE EXTENSION vector")
                conn.commit()
                print("Vector extension created successfully!")
            except psycopg2.Error as e:
                print(f"Failed to create vector extension: {e}")
                print("Please create the extension manually as superuser:")
                print("sudo -u postgres psql -d resume_db -c 'CREATE EXTENSION vector;'")
                exit()
        else:
            print("Vector extension is already installed!")

        # Define tables in CORRECT ORDER (skills first, then tables that reference it)
        tables = [
            ("users", """
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(255) PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("skills","""
            CREATE TABLE IF NOT EXISTS skills (
                skill_id SERIAL PRIMARY KEY,
                skill VARCHAR(100) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("resumes", """
            CREATE TABLE IF NOT EXISTS resumes (
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
                combined_embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("resume_summary", """
            CREATE TABLE IF NOT EXISTS resume_summary (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
                summary TEXT,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("resume_skills", """
            CREATE TABLE IF NOT EXISTS resume_skills (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
                skill_id INTEGER REFERENCES skills(skill_id) ON DELETE CASCADE,
                skill JSONB,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("resume_skills_persona", """
            CREATE TABLE IF NOT EXISTS resume_skills_persona (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
                skill_id INTEGER REFERENCES skills(skill_id) ON DELETE CASCADE,
                skill TEXT,
                rating NUMERIC(5,2) CHECK (rating >= 0 AND rating <= 100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("resume_experience", """
            CREATE TABLE IF NOT EXISTS resume_experience (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
                title VARCHAR(255),
                company VARCHAR(255),
                description TEXT,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("resume_total_experience", """
            CREATE TABLE IF NOT EXISTS resume_total_experience (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
                years VARCHAR(255),
                description TEXT,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("resume_education", """
            CREATE TABLE IF NOT EXISTS resume_education (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
                degree VARCHAR(255),
                institution VARCHAR(255),
                description TEXT,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("resume_certifications", """
            CREATE TABLE IF NOT EXISTS resume_certifications (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
                certification JSONB,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("resume_projects", """
            CREATE TABLE IF NOT EXISTS resume_projects (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
                name VARCHAR(255),
                description TEXT,
                year VARCHAR(50),
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
        ]

        for i, (table_name, table_sql) in enumerate(tables, 1):
            try:
                cursor.execute(table_sql)
                print(f"✓ Table {i}/{len(tables)}: {table_name} created successfully")
            except psycopg2.Error as e:
                print(f"✗ Table {i}/{len(tables)}: {table_name} failed - {e}")
                conn.rollback()
                continue

        conn.commit()

        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        created_tables = [row[0] for row in cursor.fetchall()]
        print(f"\nTables in database: {created_tables}")

    print("\n✓ All tables processed successfully!")
    conn.close()

except psycopg2.Error as e:
    print(f"Error connecting to database: {e}")
    exit()