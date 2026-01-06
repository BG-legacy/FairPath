"""
Example service - business logic goes here
Keeping routes thin and services doing the actual work
"""
from models.schemas import ExampleRequest, ExampleResponse
from datetime import datetime
from typing import Dict, Any

class ExampleService:
    """Example service class - replace this with your actual services"""
    
    async def process_data(self, request: ExampleRequest) -> Dict[str, Any]:
        """
        Process the request data
        This is where you'd do actual work like calling OpenAI, DB operations, etc
        Right now it's just returning some dummy data
        """
        # just an example - replace with real logic
        # In a real service, I'd probably call OpenAI here or do DB queries
        result = {
            "result": f"Processed: {request.text}",
            "processed_at": datetime.now(),
            "count": request.count,
            "optional": request.optional_field or "not provided"
        }
        
        return result

