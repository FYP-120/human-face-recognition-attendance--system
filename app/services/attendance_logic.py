from datetime import datetime
from app.services.face_matcher import cosine_similarity
from app.services.face_embedder import get_embedding, get_all_embeddings
from app.crud.attendance_crud import AttendanceCRUD

THRESHOLD = 0.6

attendance_crud = AttendanceCRUD()

def process_attendance(face_image, student_embeddings):
    embedding = get_embedding(face_image)
    if embedding is None:
        return "No face embedding found"

    best_score = 0
    best_student = None

    for student_id, saved_embedding in student_embeddings.items():
        score = cosine_similarity(embedding, saved_embedding)
        if score > best_score:
            best_score = score
            best_student = student_id

    if best_score >= THRESHOLD:
        if not attendance_crud.check_attendance(best_student, datetime.now()):
            attendance_crud.mark_attendance({
                "student_id": best_student,
                "date": datetime.now(),
                "status": "Present"
            })
            return f"Attendance marked for {best_student}"
        return f"{best_student} already marked"
    
    return "Unknown face detected"


def process_multiple_faces(face_image, student_embeddings):
    """
    Process multiple faces in an image and match them against student embeddings
    Args:
        face_image: numpy array of the image (RGB format)
        student_embeddings: dict mapping student_id to embeddings
    Returns:
        List of dicts containing results for each detected face
    """
    all_embeddings = get_all_embeddings(face_image)
    
    if not all_embeddings:
        return [{"status": "error", "message": "No faces detected in image"}]
    
    results = []
    today = datetime.now()
    
    for idx, (embedding, bbox) in enumerate(all_embeddings, 1):
        best_score = 0
        best_student = None
        
        # Match against all student embeddings
        for student_id, saved_embedding in student_embeddings.items():
            score = cosine_similarity(embedding, saved_embedding)
            if score > best_score:
                best_score = score
                best_student = student_id
        
        face_result = {
            "face_number": idx,
            "bbox": bbox,
            "confidence": float(best_score)
        }
        
        if best_score >= THRESHOLD:
            face_result["student_id"] = best_student
            face_result["status"] = "recognized"
            
            # Check if already marked
            already_marked = attendance_crud.check_attendance(best_student, today)
            face_result["already_marked"] = already_marked
            
            if not already_marked:
                try:
                    attendance_crud.mark_attendance({
                        "student_id": best_student,
                        "date": today,
                        "status": "Present"
                    })
                    face_result["message"] = f"Attendance marked for {best_student}"
                except Exception as e:
                    face_result["message"] = f"Recognized as {best_student} but DB error: {str(e)}"
            else:
                face_result["message"] = f"{best_student} already marked today"
        else:
            face_result["status"] = "unknown"
            face_result["message"] = "Unknown face - not in database"
        
        results.append(face_result)
    
    return results
