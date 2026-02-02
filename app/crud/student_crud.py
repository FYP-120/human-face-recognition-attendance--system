from app.core.database import get_collection
from app.models.student import StudentModel

collection=get_collection("students")

class StudentCRUD:
    def create_student(self, student:StudentModel):
        collection.insert_one(student.dict())
        
    def get_student_by_id(self, student_id:str):
        return collection.find_one({"student_id":student_id},{"_id":0})
    
    
    