import psycopg2
from psycopg2 import sql
import sys

def create_database():
    """Create the jd_db database if it doesn't exist"""
    try:
        # Connect to the default postgres database
        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="dmns",
            password="dmns",
            port=5432
        )
        conn.autocommit = True
        
        with conn.cursor() as cursor:
            # Check if jd_db exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'jd_db'")
            exists = cursor.fetchone()
            
            if not exists:
                print("Database 'jd_db' not found. Creating...")
                cursor.execute("CREATE DATABASE jd_db")
                print("Database 'jd_db' created successfully!")
            else:
                print("Database 'jd_db' already exists.")
                
    except psycopg2.Error as e:
        print(f"Error checking/creating database: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

# First, ensure the database exists
create_database()

# Now connect to jd_db and set up the tables
try:
    conn = psycopg2.connect(
        host="localhost",
        database="jd_db",
        user="dmns",
        password="dmns",
        port=5432
    )

    with conn.cursor() as cursor:
        # Check if vector extension exists
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
                print("sudo -u postgres psql -d jd_db -c 'CREATE EXTENSION vector;'")
                exit()
        else:
            print("Vector extension is already installed!")

        # Define JD tables
        tables = [
            ("job_descriptions", """
            CREATE TABLE IF NOT EXISTS job_descriptions (
                id SERIAL PRIMARY KEY,
                discipline VARCHAR(255),
                career_path VARCHAR(255),
                designation VARCHAR(255),
                vacancy_title VARCHAR(255),
                scheduled_date DATE,
                expiration_date DATE,
                vacancy_link TEXT,
                company_details TEXT,
                combined_embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("jd_preferred_industry", """
            CREATE TABLE IF NOT EXISTS jd_preferred_industry (
                id SERIAL PRIMARY KEY,
                jd_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
                preferred_industry JSONB,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("jd_description_sections", """
            CREATE TABLE IF NOT EXISTS jd_description_sections (
                id SERIAL PRIMARY KEY,
                jd_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
                description TEXT,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("jd_compulsory_skills", """
            CREATE TABLE IF NOT EXISTS jd_compulsory_skills (
                id SERIAL PRIMARY KEY,
                jd_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
                skill JSONB,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("jd_nice_to_have_skills", """
            CREATE TABLE IF NOT EXISTS jd_nice_to_have_skills (
                id SERIAL PRIMARY KEY,
                jd_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
                skill JSONB,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("jd_optional_skills", """
            CREATE TABLE IF NOT EXISTS jd_optional_skills (
                id SERIAL PRIMARY KEY,
                jd_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
                skill JSONB,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("jd_skills", """
            CREATE TABLE IF NOT EXISTS jd_skills (
                id SERIAL PRIMARY KEY,
                jd_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
                skill JSONB,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("jd_preferred_experience", """
            CREATE TABLE IF NOT EXISTS jd_preferred_experience (
                id SERIAL PRIMARY KEY,
                jd_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
                experience TEXT,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """),
            ("jd_other_qualifications", """
            CREATE TABLE IF NOT EXISTS jd_other_qualifications (
                id SERIAL PRIMARY KEY,
                jd_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
                qualification TEXT,
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
            AND (table_name LIKE 'jd_%' OR table_name = 'job_descriptions')
            ORDER BY table_name
        """)
        created_tables = [row[0] for row in cursor.fetchall()]
        print(f"\nJD tables in database: {created_tables}")

    print("\n✓ All JD tables processed successfully!")
    conn.close()

except psycopg2.Error as e:
    print(f"Error connecting to database: {e}")
    exit()