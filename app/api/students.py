from fastapi import APIRouter, HTTPException, Depends
from app.models.student import StudentModel
from app.crud.student_crud import StudentCRUD
from app.core.security import get_current_user

router = APIRouter()
crud = StudentCRUD()


@router.post("/register")
def register_student(
    student: StudentModel,
    # current_user: str = Depends(get_current_user)
):
    if crud.get_student_by_id(student.student_id):
        raise HTTPException(status_code=400, detail="Student already exists")

    crud.create_student(student)
    return {"message": "Student registered successfully"}


@router.get("/{student_id}")
def get_student(
    student_id: str,
    # current_user: str = Depends(get_current_user)
):
    student = crud.get_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return student
