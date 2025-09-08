import psycopg2
import json
from psycopg2.extras import Json

def migrate_skills_to_persona():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="resume_db",
            user="dmns",
            password="dmns",
            port=5432
        )

        with conn.cursor() as cursor:
            # First, get all skills data from resume_skills table
            cursor.execute("""
                SELECT rs.id, rs.resume_id, rs.skill
                FROM resume_skills rs
                ORDER BY rs.resume_id
            """)
            
            skills_data = cursor.fetchall()
            print(f"Found {len(skills_data)} skill records to process")
            
            # Create a mapping of skill names to skill IDs from the skills table
            cursor.execute("SELECT skill_id, skill FROM skills")
            skill_mapping = {skill.lower(): skill_id for skill_id, skill in cursor.fetchall()}
            print(f"Loaded {len(skill_mapping)} skills from skills table")
            
            # Process each row
            for row_id, resume_id, skill_data in skills_data:
                try:
                    # Check if skill_data is already a list
                    if isinstance(skill_data, list):
                        skills_list = skill_data
                    # Check if it's a JSON string that needs parsing
                    elif isinstance(skill_data, str):
                        skills_list = json.loads(skill_data)
                    # Check if it's already a parsed JSON object (dict or list)
                    elif isinstance(skill_data, (dict, list)):
                        skills_list = skill_data
                    else:
                        print(f"⚠ Skipped row {row_id}: unknown data type: {type(skill_data)}")
                        continue
                    
                    # If it's a dictionary, extract the skills (handle different JSON structures)
                    if isinstance(skills_list, dict):
                        # Try common keys where skills might be stored
                        if 'skills' in skills_list:
                            skills_list = skills_list['skills']
                        elif 'technologies' in skills_list:
                            skills_list = skills_list['technologies']
                        elif 'languages' in skills_list:
                            skills_list = skills_list['languages']
                        else:
                            # If it's a dict but we can't find skills, use the values
                            skills_list = list(skills_list.values())
                    
                    # Ensure we have a list of skills
                    if isinstance(skills_list, list):
                        # Insert each skill as a separate row in resume_skills_persona
                        inserted_count = 0
                        for skill in skills_list:
                            if skill:  # Only insert non-empty skills
                                skill_name = str(skill).strip()
                                
                                # Look up the skill ID in our mapping (case-insensitive)
                                skill_id = None
                                if skill_name.lower() in skill_mapping:
                                    skill_id = skill_mapping[skill_name.lower()]
                                
                                # Insert into resume_skills_persona
                                cursor.execute("""
                                    INSERT INTO resume_skills_persona (resume_id, skill, skill_id, rating)
                                    VALUES (%s, %s, %s, NULL)
                                    ON CONFLICT DO NOTHING
                                """, (resume_id, skill_name, skill_id))
                                inserted_count += 1
                        
                        print(f"✓ Processed resume_id {resume_id}: {inserted_count} skills added")
                    
                    else:
                        print(f"⚠ Skipped row {row_id}: skills data is not a list or dict")
                        
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    print(f"⚠ Error processing skills for row {row_id}: {e}")
                    print(f"Data: {skill_data}")
                    continue
            
            conn.commit()
            print(f"\n✓ Successfully migrated skills to resume_skills_persona table!")
            
            # Show statistics
            cursor.execute("SELECT COUNT(*) FROM resume_skills_persona")
            total_skills = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT resume_id) FROM resume_skills_persona")
            unique_resumes = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM resume_skills_persona WHERE skill_id IS NOT NULL")
            skills_with_id = cursor.fetchone()[0]
            
            print(f"Total skills in persona table: {total_skills}")
            print(f"Skills with matching IDs: {skills_with_id} ({skills_with_id/total_skills*100:.1f}%)")
            print(f"Unique resumes with skills: {unique_resumes}")
            
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        if 'conn' in locals():
            conn.rollback()

# Function to debug the skills data structure
def debug_skills_structure():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="resume_db",
            user="dmns",
            password="dmns",
            port=5432
        )

        with conn.cursor() as cursor:
            # Check sample records with more details
            cursor.execute("""
                SELECT rs.id, rs.resume_id, rs.skill, pg_typeof(rs.skill) as data_type,
                       json_typeof(rs.skill) as json_type
                FROM resume_skills rs
                LIMIT 10
            """)
            
            sample_data = cursor.fetchall()
            print("Detailed skills data structure:")
            for row in sample_data:
                row_id, resume_id, skill_data, data_type, json_type = row
                print(f"Row {row_id}: resume_id={resume_id}")
                print(f"PostgreSQL type: {data_type}")
                print(f"JSON type: {json_type}")
                print(f"Python type: {type(skill_data)}")
                print(f"Data: {skill_data}")
                print("---")
            
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")

if __name__ == "__main__":
    # First, debug the structure to understand the data better
    print("Debugging skills data structure...")
    debug_skills_structure()
    
    # Then run the migration
    print("\nStarting migration...")
    migrate_skills_to_persona()





# import psycopg2
# import json
# from psycopg2.extras import Json

# def migrate_skills_to_persona():
#     try:
#         conn = psycopg2.connect(
#             host="localhost",
#             database="resume_db",
#             user="dmns",
#             password="dmns",
#             port=5432
#         )

#         with conn.cursor() as cursor:
#             # First, get all skills data from resume_skills table
#             cursor.execute("""
#                 SELECT rs.id, rs.resume_id, rs.skill
#                 FROM resume_skills rs
#                 ORDER BY rs.resume_id
#             """)
            
#             skills_data = cursor.fetchall()
#             print(f"Found {len(skills_data)} skill records to process")
            
#             # Process each row
#             for row_id, resume_id, skill_data in skills_data:
#                 try:
#                     # Check if skill_data is already a list
#                     if isinstance(skill_data, list):
#                         skills_list = skill_data
#                     # Check if it's a JSON string that needs parsing
#                     elif isinstance(skill_data, str):
#                         skills_list = json.loads(skill_data)
#                     # Check if it's already a parsed JSON object (dict or list)
#                     elif isinstance(skill_data, (dict, list)):
#                         skills_list = skill_data
#                     else:
#                         print(f"⚠ Skipped row {row_id}: unknown data type: {type(skill_data)}")
#                         continue
                    
#                     # If it's a dictionary, extract the skills (handle different JSON structures)
#                     if isinstance(skills_list, dict):
#                         # Try common keys where skills might be stored
#                         if 'skills' in skills_list:
#                             skills_list = skills_list['skills']
#                         elif 'technologies' in skills_list:
#                             skills_list = skills_list['technologies']
#                         elif 'languages' in skills_list:
#                             skills_list = skills_list['languages']
#                         else:
#                             # If it's a dict but we can't find skills, use the values
#                             skills_list = list(skills_list.values())
                    
#                     # Ensure we have a list of skills
#                     if isinstance(skills_list, list):
#                         # Insert each skill as a separate row in resume_skills_persona
#                         inserted_count = 0
#                         for skill in skills_list:
#                             if skill:  # Only insert non-empty skills
#                                 # Insert into resume_skills_persona (rating will be NULL initially)
#                                 cursor.execute("""
#                                     INSERT INTO resume_skills_persona (resume_id, skill, rating)
#                                     VALUES (%s, %s, NULL)
#                                     ON CONFLICT DO NOTHING
#                                 """, (resume_id, str(skill).strip()))
#                                 inserted_count += 1
                        
#                         print(f"✓ Processed resume_id {resume_id}: {inserted_count} skills added")
                    
#                     else:
#                         print(f"⚠ Skipped row {row_id}: skills data is not a list or dict")
                        
#                 except (json.JSONDecodeError, TypeError, ValueError) as e:
#                     print(f"⚠ Error processing skills for row {row_id}: {e}")
#                     print(f"Data: {skill_data}")
#                     continue
            
#             conn.commit()
#             print(f"\n✓ Successfully migrated skills to resume_skills_persona table!")
            
#             # Show statistics
#             cursor.execute("SELECT COUNT(*) FROM resume_skills_persona")
#             total_skills = cursor.fetchone()[0]
#             cursor.execute("SELECT COUNT(DISTINCT resume_id) FROM resume_skills_persona")
#             unique_resumes = cursor.fetchone()[0]
            
#             print(f"Total skills in persona table: {total_skills}")
#             print(f"Unique resumes with skills: {unique_resumes}")
            
#         conn.close()
        
#     except psycopg2.Error as e:
#         print(f"Error connecting to database: {e}")
#         if 'conn' in locals():
#             conn.rollback()

# # Function to debug the skills data structure
# def debug_skills_structure():
#     try:
#         conn = psycopg2.connect(
#             host="localhost",
#             database="resume_db",
#             user="dmns",
#             password="dmns",
#             port=5432
#         )

#         with conn.cursor() as cursor:
#             # Check sample records with more details
#             cursor.execute("""
#                 SELECT rs.id, rs.resume_id, rs.skill, pg_typeof(rs.skill) as data_type,
#                        json_typeof(rs.skill) as json_type
#                 FROM resume_skills rs
#                 LIMIT 10
#             """)
            
#             sample_data = cursor.fetchall()
#             print("Detailed skills data structure:")
#             for row in sample_data:
#                 row_id, resume_id, skill_data, data_type, json_type = row
#                 print(f"Row {row_id}: resume_id={resume_id}")
#                 print(f"PostgreSQL type: {data_type}")
#                 print(f"JSON type: {json_type}")
#                 print(f"Python type: {type(skill_data)}")
#                 print(f"Data: {skill_data}")
#                 print("---")
            
#         conn.close()
        
#     except psycopg2.Error as e:
#         print(f"Error connecting to database: {e}")

# if __name__ == "__main__":
#     # First, debug the structure to understand the data better
#     print("Debugging skills data structure...")
#     debug_skills_structure()
    
#     # Then run the migration
#     print("\nStarting migration...")
#     migrate_skills_to_persona()