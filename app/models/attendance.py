from pydantic import BaseModel
from datetime import datetime


class AttendanceModel(BaseModel):
    student_id:str
    student_name:str
    date:datetime
    status:str="Present"
    