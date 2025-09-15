"""Embeddings"""
from typing import Any, Dict, List, Tuple, Optional
import google.generativeai as genai


class EmbeddingGenerator:
    """Embedding Generation class"""
    
    def __init__(self):
        self.model = genai.embed_content
        
    def generate_embedding(self, text: str, task_type: str = "retrieval_document") -> Optional[List[float]]:
        """Generate Embedding for given text using gemini model
        
                # model="models/embedding-001","""
        try:
            if text is None or not text.strip():
                return None
                
            result = self.model(
                model="models/text-embedding-004",
                content=text,
                task_type=task_type
            )
            embedding = result["embedding"]
            print(f"Successfully generated embedding of dimension {len(embedding)}")
            return embedding

        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def create_jd_embeddings(self, jd_data: Dict[str, Any]) -> Dict[str, Any]:
        print("======================")
        try:
            embeddings_result = {
                "sections": {},
                "combined_embedding": None
            }
            
            # Create combined skills text
            compulsory_skills = jd_data.get("compulsory_skills", [])
            nice_to_have_skills = jd_data.get("nice_to_have_skills", [])
            optional_skills = jd_data.get("optional_skills", [])
            
            # Combine all skills
            all_skills = compulsory_skills + nice_to_have_skills + optional_skills
            combined_skills_text = ", ".join(all_skills)
            
            # Process each section
            sections = {
                "description": jd_data.get("description", ""),
                "compulsory_skills": ", ".join(compulsory_skills),
                "nice_to_have_skills": ", ".join(nice_to_have_skills),
                "optional_skills": ", ".join(optional_skills),
                "combined_skills": combined_skills_text,
                "preferred_experience": jd_data.get("preferred_experience", ""),
                "other_qualifications": jd_data.get("other_qualifications", ""),
                "preferred_industry": ", ".join(jd_data.get("preferred_industry", [])),
            }
            
            # Generate embeddings for each section
            for section_name, section_text in sections.items():
                if section_text.strip():
                    embedding = self.generate_embedding(section_text)
                    if embedding:
                        embeddings_result["sections"][section_name] = {
                            "embedding": embedding
                        }

            # Generate combined embedding
            combined_text = f"""
            Discipline: {jd_data.get('discipline', '')}
            Career Path: {jd_data.get('career_path', '')}
            Designation: {jd_data.get('designation', '')}
            Vacancy Title: {jd_data.get('vacancy_title', '')}
            Description: {sections['description']}
            Compulsory Skills: {sections['compulsory_skills']}
            Nice to Have Skills: {sections['nice_to_have_skills']}
            Optional Skills: {sections['optional_skills']}
            Preferred Experience: {sections['preferred_experience']}
            Other Qualifications: {sections['other_qualifications']}
            Preferred Industry: {sections['preferred_industry']}
            Company Details: {jd_data.get('company_details', '')}
            """
            
            combined_embedding = self.generate_embedding(combined_text)
            if combined_embedding:
                embeddings_result["combined_embedding"] = {
                    "embedding": combined_embedding
                }
            
            print(f"Successfully created embeddings for JD: {jd_data.get('vacancy_title')}")
            return embeddings_result

        except Exception as e:
            print(f"Failed to create JD embeddings: {e}")
            return {
                "sections": {},
                "combined_embedding": None
            }

    def create_resume_embeddings(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        print("======================", resume_data)
        try:
            embeddings_result = {
                "sections": {},
                "combined_embedding": None
            }
            
            # Helper function to safely get and clean text
            def get_clean_text(value, default=""):
                if value is None:
                    return default
                if isinstance(value, str):
                    return value.strip()
                return str(value).strip()
            
            # Process each section with safe handling for None values
            sections = {
                "summary": get_clean_text(resume_data.get("summary")),
                # "skills": ", ".join(resume_data.get("skills", [])),
                "certifications": ", ".join(resume_data.get("certifications", []))
                # "total_experience": ", ".join(resume_data.get("total_experience"))
            }
            
            # Process experience
            skill_name = ""
            for ski in resume_data.get("skills", []):
                if isinstance(ski, dict):
                    name = get_clean_text(ski.get("name"))
                    skill_name += f"{name}"
            sections["skill_name"] = skill_name
            
             # Process experience
            skill_description = ""
            for ski in resume_data.get("skills", []):
                if isinstance(ski, dict):
                    description = get_clean_text(ski.get("description"))
                    skill_description += f"{description}"
            sections["skill_description"] = skill_description
            
            # Process experience
            experience_text = ""
            for exp in resume_data.get("experience", []):
                if isinstance(exp, dict):
                    title = get_clean_text(exp.get("title"))
                    company = get_clean_text(exp.get("company"))
                    description = get_clean_text(exp.get("description"))
                    experience_text += f"{title} at {company}. {description} "
            sections["experience"] = experience_text
            
            total_experience_text = ""
            total_xp = resume_data.get("total_experience")
            if isinstance(total_xp, dict):
                years = get_clean_text(total_xp.get("years"))
                description = get_clean_text(total_xp.get("description"))
                total_experience_text = f"{years} total experience. {description}"
            sections["total_experience"] = total_experience_text
            
            
            # Process education
            education_text = ""
            for edu in resume_data.get("education", []):
                if isinstance(edu, dict):
                    degree = get_clean_text(edu.get("degree"))
                    institution = get_clean_text(edu.get("institution"))
                    education_text += f"{degree} from {institution}. "
            sections["education"] = education_text
            
            # Process projects
            projects_text = ""
            for project in resume_data.get("projects", []):
                if isinstance(project, dict):
                    name = get_clean_text(project.get("name"))
                    description = get_clean_text(project.get("description"))
                    year = get_clean_text(project.get("year"))
                    projects_text += f"{name} ({year}): {description}. "
            sections["projects"] = projects_text
            
            # Generate embeddings for each section
            for section_name, section_text in sections.items():
                if section_text and section_text.strip():  # Check if text exists and is not empty
                    embedding = self.generate_embedding(section_text)
                    if embedding:
                        embeddings_result["sections"][section_name] = {
                            "embedding": embedding
                        }
            
            # Generate combined embedding
            combined_text = f"""
            Name: {get_clean_text(resume_data.get('name'))}
            Summary: {sections['summary']}
            Skills: {sections['skill_name']} {sections['skill_description']} 
            Total Experience: {sections['total_experience']}
            Experience: {sections['experience']}
            Education: {sections['education']}
            Certifications: {sections['certifications']}
            Projects: {sections['projects']}
            """
            
            combined_embedding = self.generate_embedding(combined_text)
            if combined_embedding:
                embeddings_result["combined_embedding"] = combined_embedding
            
            print(f"Successfully created embeddings for resume: {resume_data.get('name')}")
            return embeddings_result

        except Exception as e:
            print(f"Failed to create resume embeddings: {e}")
            return {
                "sections": {},
                "combined_embedding": None
            }