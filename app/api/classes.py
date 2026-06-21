from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import re
from app.core.database import db
from app.core.security import get_current_user

router = APIRouter()

class ClassCreateRequest(BaseModel):
    class_name: str = Field(..., description="Name of the class (e.g., BSCS-8A)")

@router.post("/create")
def create_class(payload: ClassCreateRequest, current_user: str = Depends(get_current_user)):
    """
    Create a new class by dynamically creating/initializing a dedicated
    MongoDB collection for storing student records.
    """
    class_name = payload.class_name.strip()
    
    if not class_name:
        raise HTTPException(status_code=400, detail="Class name cannot be empty")
        
    # Validate the class name to prevent malicious collection names in MongoDB
    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", class_name):
        raise HTTPException(
            status_code=400, 
            detail="Class name must only contain alphanumeric characters, hyphens, underscores, or periods."
        )
        
    # Check if the collection already exists
    try:
        existing_collections = db.list_collection_names()
        if class_name in existing_collections:
            return {
                "message": f"Class '{class_name}' already exists",
                "class_name": class_name,
                "collection_name": class_name,
                "created": False
            }
        
        # Dynamically create the dedicated collection in MongoDB
        db.create_collection(class_name)
        
        return {
            "message": f"Class '{class_name}' created successfully",
            "class_name": class_name,
            "collection_name": class_name,
            "created": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create class collection: {str(e)}"
        )

@router.get("")
def list_classes(current_user: str = Depends(get_current_user)):
    """List all dynamic class names from MongoDB collections"""
    try:
        collections = db.list_collection_names()
        classes = []
        for col in collections:
            if col.startswith("students-"):
                classes.append(col.replace("students-", ""))
            elif col not in ["users", "admin", "system.indexes", "students", "attendance"]:
                classes.append(col.replace("_", "-"))
        return sorted(list(set(classes)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list classes: {str(e)}")
