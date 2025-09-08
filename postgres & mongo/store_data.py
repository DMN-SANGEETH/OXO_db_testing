from typing import Any, Dict, List
import psycopg2
import json
from psycopg2.extras import Json

def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary, handling None values"""
    if data is None:
        return default
    return data.get(key, default)

def get_or_create_skills(cursor, skills_list: List[str]) -> List[int]:
    """Get existing skill IDs or create new skills, returns list of skill IDs"""
    if not skills_list:
        return []
    
    skill_ids = []
    
    for skill in skills_list:
        if not skill or not isinstance(skill, str):
            continue
            
        # Clean up the skill name
        skill_name = skill.strip()
        if not skill_name:
            continue
            
        # Check if skill already exists
        cursor.execute("SELECT skill_id FROM skills WHERE skill = %s", (skill_name,))
        result = cursor.fetchone()
        
        if result:
            # Skill exists, get the ID
            skill_ids.append(result[0])
        else:
            # Skill doesn't exist, insert it
            cursor.execute(
                "INSERT INTO skills (skill) VALUES (%s) RETURNING skill_id",
                (skill_name,)
            )
            new_skill_id = cursor.fetchone()[0]
            skill_ids.append(new_skill_id)
            print(f"✓ Created new skill: {skill_name} (ID: {new_skill_id})")
    
    return skill_ids

def insert_resume_data(resume_json):
    """Insert resume data into the database with embeddings"""
    conn = None
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="resume_db",
            user="dmns",
            password="dmns",
            port=5432
        )
        
        with conn.cursor() as cursor:
            # Insert user if user_id is provided
            user_id = safe_get(resume_json, 'user_id')
            if user_id:
                cursor.execute("""
                    INSERT INTO users (user_id) 
                    VALUES (%s)
                    ON CONFLICT (user_id) DO NOTHING
                """, (user_id,))
                print(f"✓ User {user_id} processed")
            
            # Insert main resume data (without summary since it's in a separate table)
            cursor.execute("""
                INSERT INTO resumes (
                    user_id, first_name, last_name, full_name, email, 
                    phone, linkedin_url, industry, file_path, 
                    is_valid_resume, combined_embedding
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user_id,
                safe_get(resume_json, 'first_name'),
                safe_get(resume_json, 'last_name'),
                safe_get(resume_json, 'name'),  # Using 'name' as full_name
                safe_get(resume_json, 'email'),
                safe_get(resume_json, 'phone'),
                safe_get(resume_json, 'linkedin_url'),
                safe_get(resume_json, 'industry', []),
                safe_get(resume_json, 'file_path'),
                safe_get(resume_json, 'is_valid_resume', True),
                safe_get(resume_json, 'combined_embedding')
            ))
            
            resume_id = cursor.fetchone()[0]
            print(f"✓ Resume created with ID: {resume_id}")
            
            # Insert summary if exists and has content
            summary = safe_get(resume_json, 'summary', {})
            if summary and safe_get(summary, 'text'):
                cursor.execute("""
                    INSERT INTO resume_summary (resume_id, summary, embedding)
                    VALUES (%s, %s, %s)
                """, (
                    resume_id,
                    safe_get(summary, 'text', ''),
                    safe_get(summary, 'embedding')
                ))
                print(f"✓ Summary added for resume {resume_id}")
            
            # Insert skills if exists and has content
            skills = safe_get(resume_json, 'skills', {})
            if skills and safe_get(skills, 'text'):
                skills_list = safe_get(skills, 'text', [])
                
                if skills_list:
                    # Get or create skills and get their IDs
                    skill_ids = get_or_create_skills(cursor, skills_list)
                    print(f"✓ Processed {len(skill_ids)} skills for resume {resume_id}")
                    
                    # Insert into resume_skills table
                    for skill_id in skill_ids:
                        cursor.execute("""
                            INSERT INTO resume_skills (resume_id, skill_id, skill, embedding)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (resume_id, skill_id) DO UPDATE 
                            SET embedding = EXCLUDED.embedding,
                                skill = EXCLUDED.skill
                        """, (
                            resume_id,
                            skill_id,
                            Json(skills_list),  # Store the original skills list as JSON
                            safe_get(skills, 'embedding')  # Using the same embedding for all skills
                        ))
                    print(f"✓ Added {len(skill_ids)} skills to resume_skills for resume {resume_id}")
            
            # Insert experience if exists and has content
            experience = safe_get(resume_json, 'experience', [])
            if experience:
                exp_count = 0
                for exp in experience:
                    if exp:  # Check if experience entry is not empty
                        cursor.execute("""
                            INSERT INTO resume_experience (
                                resume_id, title, company, description, embedding
                            ) VALUES (%s, %s, %s, %s, %s)
                        """, (
                            resume_id,
                            safe_get(exp, 'title'),
                            safe_get(exp, 'company'),
                            safe_get(exp, 'description', ''),
                            safe_get(exp, 'embedding')
                        ))
                        exp_count += 1
                print(f"✓ Added {exp_count} experiences for resume {resume_id}")

            # Insert total experience if exists
            total_experience = safe_get(resume_json, 'total_experience', {})
            if total_experience and safe_get(total_experience, 'years'):
                cursor.execute("""
                    INSERT INTO resume_total_experience (resume_id, years, description, embedding)
                    VALUES (%s, %s, %s, %s)
                """, (
                    resume_id,
                    safe_get(total_experience, 'years', ''),
                    safe_get(total_experience, 'description', ''),
                    safe_get(total_experience, 'embedding')
                ))
                print(f"✓ Added total experience for resume {resume_id}")

            # Insert education if exists and has content
            education = safe_get(resume_json, 'education', [])
            if education:
                edu_count = 0
                for edu in education:
                    if edu:  # Check if education entry is not empty
                        cursor.execute("""
                            INSERT INTO resume_education (
                                resume_id, degree, institution, description, embedding
                            ) VALUES (%s, %s, %s, %s, %s)
                        """, (
                            resume_id,
                            safe_get(edu, 'degree'),
                            safe_get(edu, 'institution'),
                            safe_get(edu, 'description', ''),
                            safe_get(edu, 'embedding')
                        ))
                        edu_count += 1
                print(f"✓ Added {edu_count} education entries for resume {resume_id}")
            
            # Insert certifications if exists and has content
            certifications = safe_get(resume_json, 'certifications', {})
            if certifications and safe_get(certifications, 'text'):
                cursor.execute("""
                    INSERT INTO resume_certifications (resume_id, certification, embedding)
                    VALUES (%s, %s, %s)
                """, (
                    resume_id,
                    Json(safe_get(certifications, 'text', [])),
                    safe_get(certifications, 'embedding')
                ))
                print(f"✓ Added certifications for resume {resume_id}")
            
            # Insert projects if exists and has content
            projects = safe_get(resume_json, 'projects', [])
            if projects:
                project_count = 0
                for project in projects:
                    if project:  # Check if project entry is not empty
                        cursor.execute("""
                            INSERT INTO resume_projects (
                                resume_id, name, description, year, embedding
                            ) VALUES (%s, %s, %s, %s, %s)
                        """, (
                            resume_id,
                            safe_get(project, 'name'),
                            safe_get(project, 'description'),
                            safe_get(project, 'year', ''),
                            safe_get(project, 'embedding')
                        ))
                        project_count += 1
                print(f"✓ Added {project_count} projects for resume {resume_id}")
            
            conn.commit()
            print(f"✓ Resume data inserted successfully with ID: {resume_id}")
            return True
            
    except psycopg2.Error as e:
        print(f"Error inserting resume data: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()
            
def insert_jd_data(jd_json):
    """Insert job description data into the database with embeddings"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="jd_db",
            user="dmns",
            password="dmns",
            port=5432
        )
        
        with conn.cursor() as cursor:
            # Insert main job description data
            cursor.execute("""
                INSERT INTO job_descriptions (
                    discipline, career_path, designation, vacancy_title, scheduled_date,
                    expiration_date, vacancy_link, company_details, combined_embedding
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                safe_get(jd_json, 'discipline'),
                safe_get(jd_json, 'career_path'),
                safe_get(jd_json, 'designation'),
                safe_get(jd_json, 'vacancy_title'),
                safe_get(jd_json, 'scheduled_date'),
                safe_get(jd_json, 'expiration_date'),
                safe_get(jd_json, 'vacancy_link'),
                Json(safe_get(jd_json, 'company_details', {})),
                safe_get(jd_json, 'combined_embedding')
            ))
            
            jd_id = cursor.fetchone()[0]
            
            # Insert preferred industry if exists and has content
            preferred_industry = safe_get(jd_json, 'preferred_industry', {})
            if preferred_industry and safe_get(preferred_industry, 'text'):
                cursor.execute("""
                    INSERT INTO jd_preferred_industry (jd_id, preferred_industry, embedding)
                    VALUES (%s, %s, %s)
                """, (
                    jd_id,
                    Json(safe_get(preferred_industry, 'text', [])),
                    safe_get(preferred_industry, 'embedding')
                ))
                
            # Insert description if exists and has content
            description = safe_get(jd_json, 'description', {})
            if description and safe_get(description, 'text'):
                cursor.execute("""
                    INSERT INTO jd_description_sections (jd_id, description, embedding)
                    VALUES (%s, %s, %s)
                """, (
                    jd_id,
                    safe_get(description, 'text', ''),
                    safe_get(description, 'embedding')
                ))
                
            # Insert compulsory skills if exists and has content
            compulsory_skills = safe_get(jd_json, 'compulsory_skills', {})
            if compulsory_skills and safe_get(compulsory_skills, 'text'):
                cursor.execute("""
                    INSERT INTO jd_compulsory_skills (jd_id, skill, embedding)
                    VALUES (%s, %s, %s)
                """, (
                    jd_id,
                    Json(safe_get(compulsory_skills, 'text', [])),
                    safe_get(compulsory_skills, 'embedding')
                ))
            
            # Insert nice to have skills if exists and has content
            nice_to_have_skills = safe_get(jd_json, 'nice_to_have_skills', {})
            if nice_to_have_skills and safe_get(nice_to_have_skills, 'text'):
                cursor.execute("""
                    INSERT INTO jd_nice_to_have_skills (jd_id, skill, embedding)
                    VALUES (%s, %s, %s)
                """, (
                    jd_id,
                    Json(safe_get(nice_to_have_skills, 'text', [])),
                    safe_get(nice_to_have_skills, 'embedding')
                ))
                
            # Insert optional skills if exists and has content
            optional_skills = safe_get(jd_json, 'optional_skills', {})
            if optional_skills and safe_get(optional_skills, 'text'):
                cursor.execute("""
                    INSERT INTO jd_optional_skills (jd_id, skill, embedding)
                    VALUES (%s, %s, %s)
                """, (
                    jd_id,
                    Json(safe_get(optional_skills, 'text', [])),
                    safe_get(optional_skills, 'embedding')
                ))
                
            combined_skills = safe_get(jd_json, 'combined_skills', {})
            if combined_skills and safe_get(combined_skills, 'text'):
                cursor.execute("""
                    INSERT INTO jd_skills (jd_id, skill, embedding)
                    VALUES (%s, %s, %s)
                """, (
                    jd_id,
                    Json(safe_get(combined_skills, 'text', [])),
                    safe_get(combined_skills, 'embedding')
                ))
                
            # Insert preferred experience if exists and has content
            preferred_exp = safe_get(jd_json, 'preferred_experience', {})
            if preferred_exp and safe_get(preferred_exp, 'text'):
                cursor.execute("""
                    INSERT INTO jd_preferred_experience (jd_id, experience, embedding)
                    VALUES (%s, %s, %s)
                """, (
                    jd_id,
                    safe_get(preferred_exp, 'text', ''),
                    safe_get(preferred_exp, 'embedding')
                ))
            
            # Insert other qualifications if exists and has content
            other_qualifications = safe_get(jd_json, 'other_qualifications', {})
            if other_qualifications and safe_get(other_qualifications, 'text'):
                cursor.execute("""
                    INSERT INTO jd_other_qualifications (jd_id, qualification, embedding)
                    VALUES (%s, %s, %s)
                """, (
                    jd_id,
                    Json(safe_get(other_qualifications, 'text', [])),
                    safe_get(other_qualifications, 'embedding')
                ))
            
            conn.commit()
            print(f"✓ Job description data inserted successfully with ID: {jd_id}")
            return True
            
    except psycopg2.Error as e:
        print(f"Error inserting job description data: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


# from typing import Any, Dict
# import psycopg2
# import json
# from psycopg2.extras import Json

# def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
#     """Safely get value from dictionary, handling None values"""
#     if data is None:
#         return default
#     return data.get(key, default)

# def insert_resume_data(resume_json):
#     """Insert resume data into the database with embeddings"""
#     try:
#         conn = psycopg2.connect(
#             host="localhost",
#             database="resume_db",
#             user="dmns",
#             password="dmns",
#             port=5432
#         )
        
#         with conn.cursor() as cursor:
#             # Insert user if user_id is provided
#             user_id = safe_get(resume_json, 'user_id')
#             if user_id:
#                 cursor.execute("""
#                     INSERT INTO users (user_id) 
#                     VALUES (%s)
#                     ON CONFLICT (user_id) DO NOTHING
#                 """, (user_id,))
            
#             # Insert main resume data
#             cursor.execute("""
#                 INSERT INTO resumes (
#                     user_id, first_name, last_name, full_name, email, 
#                     phone, linkedin_url, industry, file_path, 
#                     is_valid_resume, combined_embedding
#                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#                 RETURNING id
#             """, (
#                 user_id,
#                 safe_get(resume_json, 'first_name'),
#                 safe_get(resume_json, 'last_name'),
#                 safe_get(resume_json, 'name'),  # Using 'name' as full_name
#                 safe_get(resume_json, 'email'),
#                 safe_get(resume_json, 'phone'),
#                 safe_get(resume_json, 'linkedin_url'),
#                 safe_get(resume_json, 'industry', []),
#                 safe_get(resume_json, 'file_path'),
#                 safe_get(resume_json, 'is_valid_resume', True),
#                 safe_get(resume_json, 'combined_embedding')
#             ))
            
#             resume_id = cursor.fetchone()[0]
            
#             # Insert summary if exists and has content
#             summary = safe_get(resume_json, 'summary', {})
#             if summary and safe_get(summary, 'text'):
#                 cursor.execute("""
#                     INSERT INTO resume_summary (resume_id, summary, embedding)
#                     VALUES (%s, %s, %s)
#                 """, (
#                     resume_id,
#                     safe_get(summary, 'text', ''),
#                     safe_get(summary, 'embedding')
#                 ))
            
#             # Insert skills if exists and has content
#             skills = safe_get(resume_json, 'skills', {})
#             if skills and safe_get(skills, 'text'):
#                 cursor.execute("""
#                     INSERT INTO resume_skills (resume_id, skill, embedding)
#                     VALUES (%s, %s, %s)
#                 """, (
#                     resume_id,
#                     Json(safe_get(skills, 'text', [])),
#                     safe_get(skills, 'embedding')
#                 ))
            
#             # Insert experience if exists and has content
#             experience = safe_get(resume_json, 'experience', [])
#             if experience:
#                 for exp in experience:
#                     if exp:  # Check if experience entry is not empty
#                         cursor.execute("""
#                             INSERT INTO resume_experience (
#                                 resume_id, title, company, description, embedding
#                             ) VALUES (%s, %s, %s, %s, %s)
#                         """, (
#                             resume_id,
#                             safe_get(exp, 'title'),
#                             safe_get(exp, 'company'),
#                             safe_get(exp, 'description', ''),
#                             safe_get(exp, 'embedding')
#                         ))

#             total_experience = safe_get(resume_json, 'total_experience', {})
#             if total_experience and safe_get(total_experience, 'years'):
#                 cursor.execute("""
#                     INSERT INTO resume_total_experience (resume_id, years, description, embedding)
#                     VALUES (%s, %s, %s, %s)
#                 """, (
#                     resume_id,
#                     safe_get(total_experience, 'years', ''),
#                     safe_get(total_experience, 'description', ''),
#                     safe_get(total_experience, 'embedding')
#                 ))

#             # Insert education if exists and has content
#             education = safe_get(resume_json, 'education', [])
#             if education:
#                 for edu in education:
#                     if edu:  # Check if education entry is not empty
#                         cursor.execute("""
#                             INSERT INTO resume_education (
#                                 resume_id, degree, institution, description, embedding
#                             ) VALUES (%s, %s, %s, %s, %s)
#                         """, (
#                             resume_id,
#                             safe_get(edu, 'degree'),
#                             safe_get(edu, 'institution'),
#                             safe_get(edu, 'description', ''),
#                             safe_get(edu, 'embedding')
#                         ))
            
#             # Insert certifications if exists and has content
#             certifications = safe_get(resume_json, 'certifications', {})
#             if certifications and safe_get(certifications, 'text'):
#                 cursor.execute("""
#                     INSERT INTO resume_certifications (resume_id, certification, embedding)
#                     VALUES (%s, %s, %s)
#                 """, (
#                     resume_id,
#                     Json(safe_get(certifications, 'text', [])),
#                     safe_get(certifications, 'embedding')
#                 ))
            
#             # Insert projects if exists and has content
#             projects = safe_get(resume_json, 'projects', [])
#             if projects:
#                 for project in projects:
#                     if project:  # Check if project entry is not empty
#                         cursor.execute("""
#                             INSERT INTO resume_projects (
#                                 resume_id, name, description, year, embedding
#                             ) VALUES (%s, %s, %s, %s, %s)
#                         """, (
#                             resume_id,
#                             safe_get(project, 'name'),
#                             safe_get(project, 'description'),
#                             safe_get(project, 'year', ''),
#                             safe_get(project, 'embedding')
#                         ))
            
#             conn.commit()
#             print(f"✓ Resume data inserted successfully with ID: {resume_id}")
#             return True
            
#     except psycopg2.Error as e:
#         print(f"Error inserting resume data: {e}")
#         if conn:
#             conn.rollback()
#         return False
#     finally:
#         if conn:
#             conn.close()
















# import psycopg2
# import json
# from psycopg2.extras import Json

# def insert_resume_data(resume_json):
#     """Insert resume data into the database with embeddings"""
#     try:
#         conn = psycopg2.connect(
#             host="localhost",
#             database="resume_db",
#             user="dmns",
#             password="dmns",
#             port=5432
#         )
        
#         with conn.cursor() as cursor:
#             # Insert user if user_id is provided
#             if resume_json.get('user_id'):
#                 cursor.execute("""
#                     INSERT INTO users (user_id) 
#                     VALUES (%s)
#                     ON CONFLICT (user_id) DO NOTHING
#                 """, (resume_json['user_id'],))
            
#             # Insert main resume data
#             cursor.execute("""
#                 INSERT INTO resumes (
#                     user_id, first_name, last_name, full_name, email, 
#                     phone, linkedin_url, industry, file_path, 
#                     is_valid_resume, combined_embedding
#                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#                 RETURNING id
#             """, (
#                 resume_json.get('user_id'),
#                 resume_json.get('first_name'),
#                 resume_json.get('last_name'),
#                 resume_json.get('name'),  # Using 'name' as full_name
#                 resume_json.get('email'),
#                 resume_json.get('phone'),
#                 resume_json.get('linkedin_url'),
#                 resume_json.get('industry', []),
#                 resume_json.get('file_path'),
#                 resume_json.get('is_valid_resume', True),
#                 resume_json.get('combined_embedding')
#             ))
            
#             resume_id = cursor.fetchone()[0]
            
#             if 'summary' in resume_json:
#                 cursor.execute("""
#                     INSERT INTO resume_summary (resume_id, summary, embedding)
#                     VALUES (%s, %s, %s)
#                 """, (
#                     resume_id,
#                     resume_json['summary'].get('text', ''),  # Pass the array directly
#                     resume_json['summary'].get('embedding')
#                 ))
            
#             # Insert skills (each skill gets its own row with the same embedding)
#             if 'skills' in resume_json:
#                 cursor.execute("""
#                     INSERT INTO resume_skills (resume_id, skill, embedding)
#                     VALUES (%s, %s, %s)
#                 """, (
#                     resume_id,
#                     Json(resume_json['skills'].get('text', [])),  # Pass the array directly
#                     resume_json['skills'].get('embedding')
#                 ))
            
#             # Insert experience (each experience gets its own row)
#             if 'experience' in resume_json:
#                 for exp in resume_json['experience']:
#                     cursor.execute("""
#                         INSERT INTO resume_experience (
#                             resume_id, title, company, description, embedding
#                         ) VALUES (%s, %s, %s, %s, %s)
#                     """, (
#                         resume_id,
#                         exp.get('title'),
#                         exp.get('company'),
#                         exp.get('description'),
#                         exp.get('embedding')
#                     ))
            
#             # Insert education (each education gets its own row)
#             if 'education' in resume_json:
#                 for edu in resume_json['education']:
#                     cursor.execute("""
#                         INSERT INTO resume_education (
#                             resume_id, degree, institution, description, embedding
#                         ) VALUES (%s, %s, %s, %s, %s)
#                     """, (
#                         resume_id,
#                         edu.get('degree'),
#                         edu.get('institution'),
#                         edu.get('description', ''),
#                         edu.get('embedding')
#                     ))
            
#             # Insert certifications (each certification gets its own row)
#             if 'certifications' in resume_json:
#                     cursor.execute("""
#                         INSERT INTO resume_certifications (resume_id, certification, embedding)
#                         VALUES (%s, %s, %s)
#                     """, (
#                         resume_id,
#                         Json(resume_json['certifications'].get('text', [])),
#                         resume_json.get('embedding')
#                     ))
            
#             # Insert projects (each project gets its own row)
#             if 'projects' in resume_json:
#                 for project in resume_json['projects']:
#                     cursor.execute("""
#                         INSERT INTO resume_projects (
#                             resume_id, name, description, year, embedding
#                         ) VALUES (%s, %s, %s, %s, %s)
#                     """, (
#                         resume_id,
#                         project.get('name'),
#                         project.get('description'),
#                         project.get('year', ''),
#                         project.get('embedding')
#                     ))
            
#             conn.commit()
#             print(f"✓ Resume data inserted successfully with ID: {resume_id}")
#             return True
            
#     except psycopg2.Error as e:
#         print(f"Error inserting resume data: {e}")
#         if conn:
#             conn.rollback()
#         return False
#     finally:
#         if conn:
#             conn.close()


# def insert_jd_data(jd_json):
#     """Insert job description data into the database with embeddings"""
#     try:
#         conn = psycopg2.connect(
#             host="localhost",
#             database="jd_db",
#             user="dmns",
#             password="dmns",
#             port=5432
#         )
        
#         with conn.cursor() as cursor:
#             # Insert main job description data
#             cursor.execute("""
#                 INSERT INTO job_descriptions (
#                     discipline, career_path, designation, vacancy_title, scheduled_date,
#                     expiration_date, vacancy_link, company_details, combined_embedding
#                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#                 RETURNING id
#             """, (
#                 jd_json.get('discipline'),
#                 jd_json.get('career_path'),
#                 jd_json.get('designation'),
#                 jd_json.get('vacancy_title'),
#                 jd_json.get('scheduled_date'),
#                 jd_json.get('expiration_date'),
#                 jd_json.get('vacancy_link'),
#                 Json(jd_json.get('company_details', {})),  # Convert dict to JSON
#                 jd_json.get('combined_embedding')
#             ))
            
#             jd_id = cursor.fetchone()[0]
            
#             # Insert preferred industry
#             if 'preferred_industry' in jd_json:
#                 preferred_industry = jd_json['preferred_industry']
#                 cursor.execute("""
#                     INSERT INTO jd_preferred_industry (jd_id, preferred_industry, embedding)
#                     VALUES (%s, %s, %s)
#                 """, (
#                     jd_id,
#                     Json(preferred_industry.get('text', [])),  # Use Json() wrapper
#                     preferred_industry.get('embedding')
#                 ))
                
#             # Insert description
#             if 'description' in jd_json:
#                 description = jd_json['description']
#                 cursor.execute("""
#                     INSERT INTO jd_description_sections (jd_id, description, embedding)
#                     VALUES (%s, %s, %s)
#                 """, (
#                     jd_id,
#                     description.get('text', ''),  # This should be text, not JSON
#                     description.get('embedding')
#                 ))
                
#             # Insert compulsory skills
#             if 'compulsory_skills' in jd_json:
#                 compulsory_skills = jd_json['compulsory_skills']
#                 cursor.execute("""
#                     INSERT INTO jd_compulsory_skills (jd_id, skill, embedding)
#                     VALUES (%s, %s, %s)
#                 """, (
#                     jd_id,
#                     Json(compulsory_skills.get('text', [])),  # Use Json() wrapper
#                     compulsory_skills.get('embedding')
#                 ))
            
#             # Insert nice to have skills
#             if 'nice_to_have_skills' in jd_json:
#                 nice_to_have_skills = jd_json['nice_to_have_skills']
#                 cursor.execute("""
#                     INSERT INTO jd_nice_to_have_skills (jd_id, skill, embedding)
#                     VALUES (%s, %s, %s)
#                 """, (
#                     jd_id,
#                     Json(nice_to_have_skills.get('text', [])),  # Use Json() wrapper
#                     nice_to_have_skills.get('embedding')
#                 ))
                
#             # Insert optional skills
#             if 'optional_skills' in jd_json:
#                 optional_skills = jd_json['optional_skills']
#                 cursor.execute("""
#                     INSERT INTO jd_optional_skills (jd_id, skill, embedding)
#                     VALUES (%s, %s, %s)
#                 """, (
#                     jd_id,
#                     Json(optional_skills.get('text', [])),  # Use Json() wrapper
#                     optional_skills.get('embedding')
#                 ))
                
#             # Insert preferred experience
#             if 'preferred_experience' in jd_json:
#                 preferred_exp = jd_json['preferred_experience']
#                 cursor.execute("""
#                     INSERT INTO jd_preferred_experience (jd_id, experience, embedding)
#                     VALUES (%s, %s, %s)
#                 """, (
#                     jd_id,
#                     preferred_exp.get('text', ''),  # This should be text
#                     preferred_exp.get('embedding')
#                 ))
            
#             # Insert other qualifications
#             if 'other_qualifications' in jd_json:
#                 other_qualifications = jd_json['other_qualifications']
#                 cursor.execute("""
#                     INSERT INTO jd_other_qualifications (jd_id, qualification, embedding)
#                     VALUES (%s, %s, %s)
#                 """, (
#                     jd_id,
#                     Json(other_qualifications.get('text', [])),  # Use Json() wrapper
#                     other_qualifications.get('embedding')
#                 ))
            
#             conn.commit()
#             print(f"✓ Job description data inserted successfully with ID: {jd_id}")
#             return True
            
#     except psycopg2.Error as e:
#         print(f"Error inserting job description data: {e}")
#         if conn:
#             conn.rollback()
#         return False
#     finally:
#         if conn:
#             conn.close()