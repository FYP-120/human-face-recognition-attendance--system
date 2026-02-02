import os
import numpy as np
import cv2
from app.services.face_embedder import get_embedding
from app.core.config import EMBEDDINGS_DIR

RAW_DIR="datasets/raw/"
EMBEDDINGS_FILE=os.path.join(EMBEDDINGS_DIR, "student_embeddings.npy")

if not os.path.exists(EMBEDDINGS_DIR):
    os.makedirs(EMBEDDINGS_DIR)
    
embeddings=[]
student_ids=[]

print(f"Scanning directory: {RAW_DIR}")

for student_folder in os.listdir(RAW_DIR):
    path=os.path.join(RAW_DIR,student_folder)
    if not os.path.isdir(path):
        continue
    
    print(f"\nProcessing student: {student_folder}")
    student_embeddings_count = 0
    
    for img_file in os.listdir(path):
        img_path=os.path.join(path, img_file)
        print(f"  Processing image: {img_file}...", end=" ")
        
        try:
            # Read image directly
            img = cv2.imread(img_path)
            if img is None:
                print("Failed to read image")
                continue
            
            # Convert BGR to RGB for processing
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Get embedding (insightface will detect and extract)
            emb = get_embedding(img_rgb)
            
            if emb is not None:
                embeddings.append(emb)
                student_ids.append(student_folder)
                student_embeddings_count += 1
                print("✓ Embedding generated")
            else:
                print("No face detected or failed to generate embedding")
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"  Total embeddings for {student_folder}: {student_embeddings_count}")
            
np.save(EMBEDDINGS_FILE, {"student_ids":student_ids, "embeddings":embeddings})
print(f"\n✓ Saved embeddings for {len(student_ids)} images from {len(set(student_ids))} students to {EMBEDDINGS_FILE}")

            
