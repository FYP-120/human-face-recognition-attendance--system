from fastapi import APIRouter, HTTPException, File, UploadFile, Depends, Query, Form
from pydantic import BaseModel, Field
from app.models.attendance import AttendanceModel
from app.crud.attendance_crud import AttendanceCRUD
from app.crud.student_crud import StudentCRUD
from datetime import datetime
import cv2
import numpy as np
import os
from typing import Optional, List

from app.core.security import get_current_user
from app.services.face_matcher import cosine_similarity
from app.core.config import EMBEDDINGS_DIR
from app.services.attendance_logic import process_multiple_faces

router = APIRouter()
crud = AttendanceCRUD()


# ==================== CREATE ====================

@router.post("/mark")
def mark_attendance(
    attendance: AttendanceModel,
    class_name: str = Query(..., description="Target class name"),
    current_user: str = Depends(get_current_user)
):
    """Mark attendance for a student manually"""
    today = datetime.utcnow()

    # Verify student belongs to this class's collection
    student_crud = StudentCRUD()
    student = student_crud.get_student_by_id(attendance.student_id, class_name=class_name)
    if not student:
        raise HTTPException(
            status_code=400,
            detail=f"Student '{attendance.student_id}' does not exist in class '{class_name}'"
        )

    local_crud = AttendanceCRUD(class_name)
    if local_crud.check_attendance(attendance.student_id, today, course_name=attendance.course_name, course_code=attendance.course_code):
        raise HTTPException(status_code=400, detail="Attendance already marked today")

    attendance.date = today
    attendance.status = attendance.status or "Present"
    local_crud.mark_attendance(attendance)

    return {"message": "Attendance marked successfully", "student_id": attendance.student_id, "date": str(today)}


@router.post("/mark-from-image")
async def mark_attendance_from_image(
    class_name: str = Form(..., description="Target class name"),
    file: UploadFile = File(...),
    course_name: Optional[str] = Form(None, description="Course name for attendance"),
    course_code: Optional[str] = Form(None, description="Course code for attendance"),
    current_user: str = Depends(get_current_user)
):
    """Mark attendance by uploading student image"""
    try:
        EMBEDDINGS_FILE = os.path.join(EMBEDDINGS_DIR, "student_embeddings.npy")

        if not os.path.exists(EMBEDDINGS_FILE):
            raise HTTPException(status_code=500, detail="Embeddings file not found")

        # Read and decode image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Fetch student IDs in the targeted class students-[class_name] collection
        student_crud = StudentCRUD()
        class_students = student_crud.list_students(limit=10000, class_name=class_name)
        class_student_ids = {s.get("student_id") for s in class_students if s.get("student_id")}

        # Load global embeddings
        embeddings_data = np.load(EMBEDDINGS_FILE, allow_pickle=True).item()
        student_ids = embeddings_data["student_ids"]
        embeddings = embeddings_data["embeddings"]

        # Rebuild or slice the candidate embedding matrix dynamically at runtime
        sliced_indices = [idx for idx, s_id in enumerate(student_ids) if s_id in class_student_ids]
        
        # Build sliced list of IDs and list of vectors, keeping indices aligned
        sliced_student_ids = [student_ids[idx] for idx in sliced_indices]
        sliced_embeddings = [embeddings[idx] for idx in sliced_indices]
        
        # Zip them to preserve mapping alignment
        student_embeddings = list(zip(sliced_student_ids, sliced_embeddings))

        # Process faces and mark attendance, dynamically restricting lookup
        results = process_multiple_faces(img_rgb, student_embeddings, class_name=class_name, course_name=course_name, course_code=course_code)

        return {
            "message": "Image processed successfully",
            "results": results,
            "processed_by": current_user,
            "timestamp": str(datetime.utcnow())
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


# ==================== READ ====================

@router.get("/")
def list_attendance(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=1000),
    student_id: str = Query(None),
    date: str = Query(None),
    class_name: Optional[str] = Query(None),
    course_name: Optional[str] = Query(None),
    course_code: Optional[str] = Query(None),
    current_user: str = Depends(get_current_user)
):
    """Get attendance records with optional filtering"""
    try:
        # Build filter
        filter_dict = {}
        if student_id:
            filter_dict["student_id"] = student_id
        if date:
            filter_dict["date"] = date
        if course_name:
            filter_dict["course_name"] = course_name
        if course_code:
            filter_dict["course_code"] = course_code

        local_crud = AttendanceCRUD(class_name) if class_name else crud
        records = local_crud.list_attendance(skip, limit, filter_dict)

        # Map display title format
        for record in records:
            r_class = class_name or "Unknown Class"
            r_course = record.get("course_name") or course_name or "Unknown Course"
            r_code = record.get("course_code") or course_code or "Unknown Code"
            record["display_title"] = f"Attendance for {r_class} - Course: {r_course} ({r_code})"

        return {
            "records": records, 
            "count": len(records),
            "summary": f"Attendance for {class_name} - Course: {course_name} ({course_code})" if class_name and course_name else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching records: {str(e)}")


class StudentAttendanceReport(BaseModel):
    student_id: str
    name: str
    reg_number: str
    status: str
    record_id: Optional[str] = None
    course_name: Optional[str] = None
    course_code: Optional[str] = None
    date: Optional[datetime] = None


@router.get("/report", response_model=List[StudentAttendanceReport])
def get_attendance_report(
    date: str = Query(..., description="Date (YYYY-MM-DD)"),
    subject: Optional[str] = Query(None, description="Course code or Course name"),
    class_name: str = Query(..., alias="class", description="Class program"),
    current_user: str = Depends(get_current_user)
):
    try:
        query_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    try:
        # Resolve class collections and lists
        local_crud = AttendanceCRUD(class_name)
        student_crud = StudentCRUD()
        
        # Fetch enrolled class registry students
        students_in_class = student_crud.list_students(limit=10000, class_name=class_name)
        
        # Query attendance records matching date range and subject
        start_date = query_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = query_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        query = {
            "date": {"$gte": start_date, "$lte": end_date}
        }
        if subject:
            query["$or"] = [
                {"course_code": subject},
                {"course_name": subject}
            ]
        records = list(local_crud.collection.find(query))
        
        import re
        report = []
        for s in students_in_class:
            s_id = s.get("student_id")
            s_name = s.get("name", "")
            s_reg = s.get("reg_number") or s_id
            
            # Match registered student with query attendance log status
            status = "Absent"
            record_id_val = None
            course_name_val = None
            course_code_val = None
            date_val = None
            
            clean_student_id = s_id.lstrip("0") if s_id else ""
            
            for r in records:
                r_student_id = r.get("student_id")
                if not r_student_id:
                    continue
                
                is_match = False
                if r_student_id == s_id:
                    is_match = True
                else:
                    clean_record_id = r_student_id.lstrip("0")
                    r_match = re.match(r'.*-(\d+)$', r_student_id)
                    s_match = re.match(r'.*-(\d+)$', s_id) if s_id else None
                    
                    r_suffix = r_match.group(1).lstrip("0") if r_match else clean_record_id
                    s_suffix = s_match.group(1).lstrip("0") if s_match else clean_student_id
                    
                    if r_suffix == s_suffix and r_suffix != "":
                        is_match = True
                        
                if is_match:
                    status = r.get("status", "Present")
                    record_id_val = str(r["_id"]) if "_id" in r else None
                    course_name_val = r.get("course_name")
                    course_code_val = r.get("course_code")
                    date_val = r.get("date")
                    break
                    
            report.append(StudentAttendanceReport(
                student_id=s_id,
                name=s_name,
                reg_number=s_reg,
                status=status,
                record_id=record_id_val,
                course_name=course_name_val,
                course_code=course_code_val,
                date=date_val
            ))
            
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving attendance report: {str(e)}")


@router.get("/export")
def export_attendance_excel(
    date: str = Query(..., description="Date (YYYY-MM-DD)"),
    class_name: str = Query(..., alias="class", description="Class program"),
    current_user: str = Depends(get_current_user)
):
    """
    Export attendance for all students and all subjects in a class for a specific date as an Excel spreadsheet
    """
    from app.core.database import db
    from app.crud.student_crud import StudentCRUD
    from app.crud.attendance_crud import resolve_attendance_collection
    from fastapi import HTTPException
    from fastapi.responses import StreamingResponse
    import io
    import pandas as pd
    from datetime import datetime
    import re
    
    try:
        # 1. Parse date
        try:
            query_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
            
        # 2. Fetch all registered students for this class
        student_crud = StudentCRUD()
        students = student_crud.list_students(limit=10000, class_name=class_name)
        
        # 3. Resolve degree and semester from class_name
        degree = "BSCS"
        semester = "8"
        for deg in ["BSCS", "BSSE", "BSAI"]:
            if deg in class_name.upper():
                degree = deg
                break
        m = re.search(r'\d+', class_name)
        if m:
            semester = m.group(0)
            
        # 4. Fetch subjects for this class/degree/semester
        subjects_col = db['subjects']
        sub_doc = subjects_col.find_one({"degree": degree})
        class_subjects = []
        if sub_doc:
            semesters = sub_doc.get('semesters', {})
            class_subjects = semesters.get(semester) or semesters.get(int(semester)) or []
            
        if not class_subjects:
            # Fallback
            class_subjects = [
                {"course_name": "General Class", "course_code": "GEN-101"}
            ]
            
        # 5. Fetch attendance logs for this class on this date
        start_date = query_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = query_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        resolved_col = resolve_attendance_collection(class_name)
        records = list(db[resolved_col].find({
            "date": {"$gte": start_date, "$lte": end_date}
        }))
        
        # 6. Build the grid: for each student and each subject
        data = []
        for s in students:
            s_id = s.get("student_id")
            s_name = s.get("name", "")
            s_reg = s.get("reg_number") or s_id
            
            for sub in class_subjects:
                sub_code = sub.get("course_code")
                sub_name = sub.get("course_name")
                
                # Find matching record in records for this student and subject
                status = "Absent"
                clean_student_id = s_id.lstrip("0") if s_id else ""
                
                for r in records:
                    r_student_id = r.get("student_id")
                    if not r_student_id:
                        continue
                    
                    # Match student ID
                    is_student_match = False
                    if r_student_id == s_id:
                        is_student_match = True
                    else:
                        clean_record_id = r_student_id.lstrip("0")
                        r_match = re.match(r'.*-(\d+)$', r_student_id)
                        s_match = re.match(r'.*-(\d+)$', s_id) if s_id else None
                        
                        r_suffix = r_match.group(1).lstrip("0") if r_match else clean_record_id
                        s_suffix = s_match.group(1).lstrip("0") if s_match else clean_student_id
                        
                        if r_suffix == s_suffix and r_suffix != "":
                            is_student_match = True
                            
                    # Match subject
                    is_subject_match = False
                    if is_student_match:
                        r_course_code = r.get("course_code")
                        r_course_name = r.get("course_name")
                        if r_course_code == sub_code or r_course_name == sub_name:
                            is_subject_match = True
                            
                    if is_student_match and is_subject_match:
                        status = r.get("status", "Present")
                        break
                        
                data.append({
                    "Date": date,
                    "Class": class_name,
                    "Student Name": s_name,
                    "Registration Number": s_reg,
                    "Course Code": sub_code,
                    "Course Name": sub_name,
                    "Status": status
                })
                
        # 7. Create pandas DataFrame and export as Excel
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Attendance Grid")
        output.seek(0)
        
        filename = f"attendance_grid_{class_name}_{date}.xlsx"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Access-Control-Expose-Headers': 'Content-Disposition'
        }
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Excel report: {str(e)}")


class StudentAttendanceStatusResponse(BaseModel):
    student_id: str
    name: str
    class_name: str
    subject: Optional[str] = None
    date: str
    status: str


@router.get("/student/{student_id}", response_model=List[StudentAttendanceStatusResponse])
def get_student_attendance_record(
    student_id: str,
    date: str = Query(..., description="Date (YYYY-MM-DD)"),
    subject: Optional[str] = Query(None, description="Course code or Course name"),
    current_user: str = Depends(get_current_user)
):
    try:
        query_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    try:
        # Find student details
        student_crud = StudentCRUD()
        student = student_crud.get_student_by_id(student_id)
        if not student:
            return []

        s_id = student["student_id"]
        s_name = student["name"]

        # Resolve class/section
        class_name = student.get("class_name")
        if not class_name:
            from app.core.database import db
            for col_name in db.list_collection_names():
                if col_name.startswith("students-"):
                    if db[col_name].find_one({"student_id": s_id}):
                        class_name = col_name.replace("students-", "")
                        break
        if not class_name:
            class_name = "BSCS_8B"  # fallback

        local_crud = AttendanceCRUD(class_name)

        # Query matching date range, student_id (handling suffix matching)
        import re
        clean_id = s_id.lstrip("0") if s_id else ""
        match = re.match(r'.*-(\d+)$', s_id) if s_id else None
        suffix = match.group(1).lstrip("0") if match else clean_id
        student_id_filter = {"$in": [s_id, suffix]} if suffix else s_id

        start_date = query_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = query_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        query = {
            "student_id": student_id_filter,
            "date": {"$gte": start_date, "$lte": end_date}
        }
        if subject:
            query["$or"] = [
                {"course_code": subject},
                {"course_name": subject}
            ]

        records = list(local_crud.collection.find(query))

        if subject and not records:
            return [StudentAttendanceStatusResponse(
                student_id=s_id,
                name=s_name,
                class_name=class_name,
                subject=subject,
                date=date,
                status="Absent"
            )]

        return [
            StudentAttendanceStatusResponse(
                student_id=s_id,
                name=s_name,
                class_name=class_name,
                subject=r.get("course_name") or r.get("course_code") or "Unknown",
                date=date,
                status=r.get("status", "Absent")
            )
            for r in records
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving student attendance: {str(e)}")


@router.get("/{attendance_id}")
def get_attendance(
    attendance_id: str,
    class_name: Optional[str] = Query(None),
    current_user: str = Depends(get_current_user)
):
    """Get a specific attendance record by ID or student ID"""
    try:
        local_crud = AttendanceCRUD(class_name) if class_name else crud
        record = local_crud.get_attendance_by_id(attendance_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"Attendance record not found for {attendance_id}")
        
        # Convert ObjectId to string for JSON serialization
        if "_id" in record:
            record["_id"] = str(record["_id"])
        
        return record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching record: {str(e)}")


class AttendanceUpdateRequest(BaseModel):
    status: Optional[str] = Field(default=None)
    course_name: Optional[str] = Field(default=None)
    course_code: Optional[str] = Field(default=None)
    date: Optional[datetime] = Field(default=None)

# ==================== UPDATE ====================

@router.patch("/{attendance_id}")
def update_attendance(
    attendance_id: str,
    payload: AttendanceUpdateRequest,
    class_name: Optional[str] = Query(None),
    current_user: str = Depends(get_current_user)
):
    """Manually correct or update an existing attendance record (changing status, subject, etc.)"""
    try:
        local_crud = AttendanceCRUD(class_name) if class_name else crud
        record = local_crud.get_attendance_by_id(attendance_id)
        if not record:
            raise HTTPException(status_code=404, detail="Attendance record not found")

        # Clean the incoming payload in the attendance route handler by explicitly filtering out "string" values
        update_data = {k: v for k, v in payload.dict(exclude_unset=True).items() if v != "string" and v is not None}

        if not update_data:
            return {"message": "No update fields provided", "attendance_id": attendance_id}

        # Update MongoDB using {"$set": update_data} via update_one so unprovided fields remain completely untouched
        result = local_crud.collection.update_one(
            {"_id": record["_id"]},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=400, detail="Failed to update attendance")

        return {"message": "Attendance updated successfully", "attendance_id": attendance_id, "updated_fields": update_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating record: {str(e)}")


# ==================== DELETE ====================

@router.delete("/{student_id}")
def delete_attendance(
    student_id: str,
    class_name: str = Query(..., description="Target class name"),
    course_name: Optional[str] = Query(None, description="Course name"),
    course_code: Optional[str] = Query(None, description="Course code"),
    current_user: str = Depends(get_current_user)
):
    """Delete a specific attendance record manually by student ID, class, and course details"""
    try:
        local_crud = AttendanceCRUD(class_name)
        
        # Build query matching student_id and course details
        query = {"student_id": student_id}
        if course_name:
            query["course_name"] = course_name
        if course_code:
            query["course_code"] = course_code
            
        result = local_crud.collection.delete_one(query)
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Attendance record not found")
            
        return {
            "message": "Attendance record deleted successfully",
            "student_id": student_id,
            "class_name": class_name,
            "course_name": course_name,
            "course_code": course_code
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting record: {str(e)}")
