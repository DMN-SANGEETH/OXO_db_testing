from pymongo import MongoClient

# # client = MongoClient("mongodb+srv://sangeeth-oxo:OXO-AI12san@ml-oxo-dev-cluster.bbokc7m.mongodb.net/?retryWrites=true&w=majority&appName=ml-oxo-dev-cluster")
# client = MongoClient("mongodb+srv://oxo_ai:uKYo6xRy1SOpirjM@cluster-ai-recruitment.ygmwer8.mongodb.net/?retryWrites=true&w=majority")from pymongo import MongoClient
import json

client = MongoClient("mongodb+srv://sangeeth-oxo:OXO-AI12san@ml-oxo-dev-cluster.bbokc7m.mongodb.net/?retryWrites=true&w=majority&appName=ml-oxo-dev-cluster")

db = client["recruitment_platform"]
collection = db["extract-resumes"]

def debug_atlas_search():
    print("🔍 DEBUGGING ATLAS SEARCH")
    print("=" * 50)
    
    # Step 1: Check if documents exist
    print("Step 1: Checking documents...")
    doc_count = collection.count_documents({})
    print(f"Total documents in collection: {doc_count}")
    
    if doc_count == 0:
        print("❌ No documents found!")
        return
    
    # Step 2: Check a sample document structure
    print("\nStep 2: Sample document structure...")
    sample = collection.find_one({})
    if sample:
        print(f"✅ Sample document keys: {list(sample.keys())}")
        print(f"Name: {sample.get('name', 'N/A')}")
        print(f"Skills (first 3): {sample.get('skills', [])[:3]}")
    
    # Step 3: Test different search approaches
    print("\nStep 3: Testing different search queries...")
    
    # Test 1: Basic text search without index specification
    test_basic_search()
    
    # Test 2: With index name
    test_with_index_name()
    
    # Test 3: Simple compound search
    test_compound_search()
    
    # Step 4: List available indexes
    print("\nStep 4: Checking available indexes...")
    try:
        indexes = list(collection.list_indexes())
        print(f"Available indexes: {len(indexes)}")
        for idx in indexes:
            print(f"  - {idx.get('name', 'unnamed')}: {idx.get('key', {})}")
    except Exception as e:
        print(f"Error listing indexes: {e}")

def test_basic_search():
    print("\n--- Test 1: Basic search (no index specified) ---")
    pipeline = [
        {
            "$search": {
                "text": {
                    "query": "AI",
                    "path": {"wildcard": "*"}
                }
            }
        },
        {"$limit": 1},
        {"$project": {"name": 1, "score": {"$meta": "searchScore"}}}
    ]
    
    try:
        results = list(collection.aggregate(pipeline))
        if results:
            print(f"✅ Found result: {results[0].get('name')} (score: {results[0].get('score', 0):.2f})")
        else:
            print("❌ No results")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_with_index_name():
    print("\n--- Test 2: With explicit index name ---")
    
    # Try common index names
    possible_index_names = ["default", "resume_search_index", "search_index"]
    
    for index_name in possible_index_names:
        print(f"  Trying index: '{index_name}'")
        pipeline = [
            {
                "$search": {
                    "index": index_name,
                    "text": {
                        "query": "Python",
                        "path": ["skills"]
                    }
                }
            },
            {"$limit": 1},
            {"$project": {"name": 1, "skills": 1, "score": {"$meta": "searchScore"}}}
        ]
        
        try:
            results = list(collection.aggregate(pipeline))
            if results:
                print(f"    ✅ Success with '{index_name}': {results[0].get('name')}")
                return True
            else:
                print(f"    ❌ No results with '{index_name}'")
        except Exception as e:
            print(f"    ❌ Error with '{index_name}': {e}")
    
    return False

def test_compound_search():
    print("\n--- Test 3: Compound search ---")
    pipeline = [
        {
            "$search": {
                "compound": {
                    "should": [
                        {"text": {"query": "AI", "path": "skills"}},
                        {"text": {"query": "Python", "path": "skills"}},
                        {"text": {"query": "Machine Learning", "path": "skills"}}
                    ]
                }
            }
        },
        {"$limit": 1},
        {"$project": {"name": 1, "skills": 1, "score": {"$meta": "searchScore"}}}
    ]
    
    try:
        results = list(collection.aggregate(pipeline))
        if results:
            print(f"✅ Compound search works: {results[0].get('name')}")
        else:
            print("❌ Compound search - no results")
    except Exception as e:
        print(f"❌ Compound search error: {e}")

def check_search_indexes():
    print("\n--- Checking Search Indexes via Atlas Admin API ---")
    print("Note: This requires additional setup, but here's what to check manually:")
    print("1. Go to MongoDB Atlas Dashboard")
    print("2. Navigate to your cluster -> Search tab")
    print("3. Verify index status is 'Active' (not Building or Failed)")
    print("4. Check index definition includes the fields you're searching")

def suggest_solutions():
    print("\n" + "=" * 50)
    print("🛠️  POSSIBLE SOLUTIONS:")
    print("=" * 50)
    
    print("\n1. ✅ INDEX CREATION ISSUES:")
    print("   - Index might still be building (wait 2-5 minutes)")
    print("   - Index failed to create (check Atlas dashboard)")
    print("   - Wrong index name in code")
    
    print("\n2. ✅ FIELD PATH ISSUES:")
    print("   - Skills field might be array - try different path syntax")
    print("   - Check exact field names in your document")
    
    print("\n3. ✅ FREE TIER LIMITATIONS:")
    print("   - Maximum 3 search indexes on M0")
    print("   - Search performance might be slower")
    
    print("\n4. ✅ QUICK FIXES TO TRY:")
    print("   - Use wildcard path: {'wildcard': '*'}")
    print("   - Try without specifying index name")
    print("   - Use exact field names from your document")
    
    print("\n5. ✅ CREATE SIMPLE INDEX:")
    print("   Go to Atlas -> Search -> Create Index with this config:")
    print("   {")
    print('     "mappings": {')
    print('       "dynamic": true')
    print("     }")
    print("   }")

if __name__ == "__main__":
    debug_atlas_search()
    suggest_solutions()