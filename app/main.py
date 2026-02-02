from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api import students, attendance, auth
import os

app=FastAPI(title="Human Face Recognition Attendance System ")

# Add CORS middleware to allow browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth",tags=["Authentication"])
app.include_router(students.router, prefix="/students", tags=["Students"])
app.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])

# Add face detection endpoint at root level for the simple detect page
from fastapi import File, UploadFile
import cv2
import numpy as np
from app.services.face_embedder import get_embedding
from app.services.face_matcher import cosine_similarity
from app.core.config import EMBEDDINGS_DIR

#we need to change the code below

@app.post("/detect-face", tags=["Attendance"])
async def detect_face_root(file: UploadFile = File(...)):
    """Detect and match multiple faces with student database"""
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"faces_detected": 0, "message": "Invalid image", "faces": []}
        
        height, width = img.shape[:2]
        if width > 640:
            scale = 640 / width
            img = cv2.resize(img, (640, int(height * scale)))
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Import get_all_embeddings for multiple face detection
        from app.services.face_embedder import get_all_embeddings
        face_results = get_all_embeddings(img_rgb)
        
        num_faces = len(face_results)
        
        if num_faces == 0:
            return {
                "faces_detected": 0,
                "message": "No faces found in the image",
                "faces": []
            }
        
        # Load student embeddings for matching
        EMBEDDINGS_FILE = os.path.join(EMBEDDINGS_DIR, "student_embeddings.npy")
        if not os.path.exists(EMBEDDINGS_FILE):
            # Return detection without matching
            faces_info = []
            for idx, (emb, bbox) in enumerate(face_results, 1):
                faces_info.append({
                    "face_number": idx,
                    "bbox": bbox,
                    "matched": False,
                    "message": "Database not found"
                })
            return {
                "faces_detected": num_faces,
                "message": f"Detected {num_faces} face(s) but no student database found",
                "faces": faces_info
            }
        
        # Load embeddings
        data = np.load(EMBEDDINGS_FILE, allow_pickle=True).item()
        THRESHOLD = 0.6
        
        # Match each detected face
        faces_info = []
        for idx, (emb, bbox) in enumerate(face_results, 1):
            best_score = 0
            best_student = None
            
            # Find best match for this face
            for s_id, s_emb in zip(data["student_ids"], data["embeddings"]):
                score = cosine_similarity(emb, s_emb)
                if score > best_score:
                    best_score = score
                    best_student = s_id
            
            face_info = {
                "face_number": idx,
                "bbox": bbox,
                "confidence": round(float(best_score), 3)
            }
            
            if best_score >= THRESHOLD:
                face_info["matched"] = True
                face_info["student_id"] = best_student
                face_info["message"] = f"Student {best_student}"
            else:
                face_info["matched"] = False
                face_info["message"] = "Unknown"
            
            faces_info.append(face_info)
        
        recognized_count = sum(1 for f in faces_info if f["matched"])
        
        return {
            "faces_detected": num_faces,
            "recognized": recognized_count,
            "message": f"Detected {num_faces} face(s): {recognized_count} recognized",
            "faces": faces_info
        }
            
    except Exception as e:
        return {"faces_detected": 0, "message": f"Error: {str(e)}", "faces": []}


@app.get("/", tags=["READ"])
def root():
    return {"message":"Welcome to Face Recognition Attendance System"}

@app.get("/detect", response_class=HTMLResponse, tags=["READ"])
async def face_detect_page():
    """Simple face detection test page"""
    try:
        html_path = os.path.join("templates", "detect.html")
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                return f.read()
        return "<h1>Face detection page not found</h1>"
    except Exception as e:
        return f"<h1>Error loading page</h1><p>{str(e)}</p>"

@app.get("/camera", response_class=HTMLResponse, tags=["READ"])
async def camera_page():
    try:
        html_path = os.path.join("templates", "index.html")
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                return f.read()
        return "<h1>Camera page not found</h1><p>File path: " + html_path + "</p>"
    except Exception as e:
        return f"<h1>Error loading camera page</h1><p>{str(e)}</p>"

