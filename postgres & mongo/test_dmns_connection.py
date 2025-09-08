import psycopg2

def test_connection():
    try:
        # Connect using dmns as both username and password
        connection = psycopg2.connect(
            host="localhost",
            database="resume_db",
            user="dmns",
            password="dmns",  # Using 'dmns' as password
            port=5432
        )
        
        print("✅ Successfully connected with username: dmns, password: dmns")
        
        # Test the connection
        cursor = connection.cursor()
        cursor.execute("SELECT current_user, current_database();")
        user, db = cursor.fetchone()
        print(f"👤 Connected as: {user}")
        print(f"📊 Database: {db}")
        
        # Check vector extension
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        if cursor.fetchone():
            print("✅ Vector extension is enabled")
        else:
            print("❌ Vector extension not found")
        
        cursor.close()
        connection.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        return False
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    test_connection()