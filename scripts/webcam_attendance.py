"""
Real-time webcam attendance marking system
Press 'q' to quit, 's' to capture and mark attendance
"""
import cv2
import numpy as np
import os
from datetime import datetime
from app.services.face_embedder import get_all_embeddings
from app.services.face_matcher import cosine_similarity
from app.crud.attendance_crud import AttendanceCRUD
from app.core.config import EMBEDDINGS_DIR

# Load embeddings
EMBEDDINGS_FILE = os.path.join(EMBEDDINGS_DIR, "student_embeddings.npy")

if not os.path.exists(EMBEDDINGS_FILE):
    print(f"Error: Embeddings file not found at {EMBEDDINGS_FILE}")
    print("Please run 'python -m ml.train_embeddings' first to generate embeddings.")
    exit(1)

data = np.load(EMBEDDINGS_FILE, allow_pickle=True).item()
attendance_crud = AttendanceCRUD()

# Threshold for face matching
THRESHOLD = 0.6

# Initialize webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam")
    exit(1)

print("Webcam Attendance System Started")
print("Press 's' to capture and mark attendance")
print("Press 'q' to quit")

while True:
    ret, frame = cap.read()
    
    if not ret:
        print("Error: Failed to capture frame")
        break
    
    # Display frame
    cv2.putText(frame, "Press 's' to mark attendance, 'q' to quit", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow('Attendance System', frame)
    
    key = cv2.waitKey(30) & 0xFF
    
    if key == ord('q'):
        print("Exiting...")
        break
    elif key == ord('s'):
        print("\nCapturing and processing...")
        
        # Convert BGR to RGB for face detection
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect all faces and get embeddings
        face_results = get_all_embeddings(frame_rgb)
        
        if len(face_results) == 0:
            print("No face detected. Please position your face properly.")
            cv2.putText(frame, "No face detected!", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow('Attendance System', frame)
            cv2.waitKey(2000)
            continue
        
        print(f"\n{'='*50}")
        print(f"Detected {len(face_results)} face(s) in frame")
        print(f"{'='*50}")
        
        # Create a copy of frame for drawing
        display_frame = frame.copy()
        
        for idx, (emb, bbox) in enumerate(face_results, 1):
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            
            # Match with database
            best_score = 0
            best_student = None
            
            for s_id, s_emb in zip(data["student_ids"], data["embeddings"]):
                score = cosine_similarity(emb, s_emb)
                if score > best_score:
                    best_score = score
                    best_student = s_id
            
            print(f"\nFace {idx}:")
            print(f"  Position: ({x1}, {y1}) to ({x2}, {y2})")
            print(f"  Best match: {best_student} (confidence: {best_score:.2f})")
            
            if best_score >= THRESHOLD:
                # Check if already marked
                if not attendance_crud.check_attendance(best_student, datetime.now()):
                    # Mark attendance
                    attendance_crud.mark_attendance({
                        "student_id": best_student,
                        "date": datetime.now(),
                        "status": "Present"
                    })
                    print(f"  ✓ Attendance marked for Student ID: {best_student}")
                    
                    # Draw green box for marked student
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(display_frame, f"{best_student} - Marked", 
                               (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                else:
                    print(f"  ! Student {best_student} already marked today")
                    
                    # Draw orange box for already marked
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
                    cv2.putText(display_frame, f"{best_student} - Already marked", 
                               (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            else:
                print(f"  ✗ Unknown face (confidence too low: {best_score:.2f})")
                
                # Draw red box for unknown face
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(display_frame, "Unknown", 
                           (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        print(f"{'='*50}\n")
        cv2.imshow('Attendance System', display_frame)
        cv2.waitKey(3000)

# Release resources
cap.release()
cv2.destroyAllWindows()
print("\nWebcam closed.")
