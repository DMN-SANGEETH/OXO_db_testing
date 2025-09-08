import psycopg2
from psycopg2 import sql
import sys

def run_migration():
    """Simple database migration that creates everything needed"""
    
    # Database configuration
    DB_HOST = "localhost"
    DB_PORT = 5432
    DB_NAME = "resume_db"
    DB_USER = "dmns"
    DB_PASSWORD = "dmns"
    
    
    # Step 1: Try to connect as superuser to create database and extension
    superuser_success = False
    try:
        print("📋 Attempting superuser connection...")
        admin_conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database="resume_db",  # Connect to default postgres database
            user="dmns",      # Try postgres superuser
            password="dmns"           # Usually no password for local postgres
        )
        admin_conn.autocommit = True
        
        with admin_conn.cursor() as cursor:
            # Create database if not exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
            if not cursor.fetchone():
                cursor.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(DB_NAME),
                    sql.Identifier(DB_USER)
                ))
                print(f"✅ Database '{DB_NAME}' created with owner '{DB_USER}'")
            else:
                print(f"ℹ️  Database '{DB_NAME}' already exists")
        
        admin_conn.close()
        
        # Connect to target database as superuser to create extension
        admin_conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user="dmns",
            password="dmns"
        )
        admin_conn.autocommit = True
        
        with admin_conn.cursor() as cursor:
            # Create vector extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            print("✅ Vector extension created/verified")
        
        admin_conn.close()
        superuser_success = True
        
    except psycopg2.Error as e:
        print(f"⚠️  Superuser connection failed: {e}")
        print("📋 Will try alternative approach...")
    
    # Step 2: Connect as regular user to create tables
    try:
        print("📋 Connecting as regular user...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        
        # If superuser connection failed, try to create extension as regular user
        if not superuser_success:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    print("✅ Vector extension created/verified")
            except psycopg2.Error as e:
                print(f"❌ Could not create vector extension: {e}")
                print("🔧 Please run this SQL as superuser: CREATE EXTENSION IF NOT EXISTS vector;")
                return False
        
        # Step 3: Create all tables
        print("📋 Creating tables...")
        
        tables = [
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(255) PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
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
            """,
            """
            CREATE TABLE IF NOT EXISTS resume_skills (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
                skill VARCHAR(255),
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS resume_experience (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
                title VARCHAR(255),
                company VARCHAR(255),
                description TEXT,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS resume_education (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
                degree VARCHAR(255),
                institution VARCHAR(255),
                description TEXT,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS resume_certifications (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
                certification VARCHAR(255),
                description TEXT,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS resume_projects (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
                name VARCHAR(255),
                description TEXT,
                year VARCHAR(50),
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        with conn.cursor() as cursor:
            for i, table_sql in enumerate(tables, 1):
                cursor.execute(table_sql)
                table_name = table_sql.split()[5]  # Extract table name
                print(f"✅ Table {i}/{len(tables)}: {table_name}")
        
        # Step 4: Create indexes
        print("📋 Creating indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_resumes_combined_embedding ON resumes USING ivfflat (combined_embedding vector_cosine_ops)",
            "CREATE INDEX IF NOT EXISTS idx_skills_resume_id ON resume_skills(resume_id)",
            "CREATE INDEX IF NOT EXISTS idx_experience_resume_id ON resume_experience(resume_id)",
            "CREATE INDEX IF NOT EXISTS idx_education_resume_id ON resume_education(resume_id)",
            "CREATE INDEX IF NOT EXISTS idx_certifications_resume_id ON resume_certifications(resume_id)",
            "CREATE INDEX IF NOT EXISTS idx_projects_resume_id ON resume_projects(resume_id)"
        ]
        
        with conn.cursor() as cursor:
            for i, index_sql in enumerate(indexes, 1):
                try:
                    cursor.execute(index_sql)
                    print(f"✅ Index {i}/{len(indexes)} created")
                except psycopg2.Error as e:
                    print(f"⚠️  Index {i} failed: {e}")
        
        # Step 5: Test everything
        print("📋 Running tests...")
        
        with conn.cursor() as cursor:
            # Test basic connection
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL version: {version[:50]}...")
            
            # Test vector extension
            cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
            if cursor.fetchone():
                print("✅ Vector extension is active")
            else:
                print("❌ Vector extension not found")
            
            # Test tables
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            print(f"✅ Found {len(tables)} tables: {', '.join([t[0] for t in tables])}")
        
        conn.close()
        print("\n🎉 Database migration completed successfully!")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    """Main function to run migration"""
    print("=" * 60)
    print("           DATABASE MIGRATION SCRIPT")
    print("=" * 60)
    
    try:
        success = run_migration()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("Your database is ready to use.")
        else:
            print("\n" + "=" * 60)
            print("❌ MIGRATION FAILED!")
            print("=" * 60)
            print("Check the error messages above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()