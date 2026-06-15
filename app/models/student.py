from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class StudentModel(BaseModel):
    student_id:str
    name:str
    embedding:Optional[List[float]]=[]
    created_at:Optional[datetime]=Field(default_factory=datetime.utcnow)

class StudentListOut(BaseModel):
    student_id: str
    name: str
    reg_number: Optional[str] = None
    image_paths: Optional[List[str]] = []
    class_name: Optional[str] = None
    created_at: Optional[datetime] = None

class StudentsListResponse(BaseModel):
    students: List[StudentListOut]
    count: int