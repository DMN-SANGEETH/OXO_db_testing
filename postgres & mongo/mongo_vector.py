from pymongo import MongoClient
import numpy as np
from pprint import PrettyPrinter

# Initialize client
client = MongoClient("mongodb+srv://sangeeth-oxo:OXO-AI12san@ml-oxo-dev-cluster.bbokc7m.mongodb.net/?retryWrites=true&w=majority&appName=ml-oxo-dev-cluster")
db = client["recruitment_platform"]
collection = db["extract-resumes"]

printer = PrettyPrinter()

# Example embedding to search against (replace with your actual query embedding)
query_embedding = [
    0.012345678, -0.023456789, 0.034567890,  # Your embedding values here...
    # ... should match the dimensions of your stored embeddings
] * 128  # Just an example - use real embeddings!

# Vector search pipeline
pipeline = [
    {
        "$vectorSearch": {
            "index": "vector_index",
            "path": "embedding",
            "queryVector": query_embedding,
            "numCandidates": 100,
            "limit": 5
        }
    },
    {
        "$project": {
            "name": 1,
            "skills": 1,
            "score": {"$meta": "vectorSearchScore"}  # Include similarity score
        }
    }
]

try:
    results = collection.aggregate(pipeline)
    for result in results:
        printer.pprint(result)
except Exception as e:
    print(f"Error: {e}")