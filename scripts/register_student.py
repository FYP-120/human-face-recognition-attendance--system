import argparse
from app.crud.student_crud import StudentCRUD
from app.services.face_detector import detect_faces
from app.services.face_embedder import get_embedding
from app.models.student import StudentModel


crud=StudentCRUD()

parser=argparse.ArgumentParser()
parser.add_argument("--id",required=True)
parser.add_argument("--name",required=True)
parser.add_argument("--image", required=True)
args=parser.parse_args()


faces=detect_faces(args.image)
if len(faces)==0:
    print("NO face detected")
    exit()
    
embedding=get_embedding(faces[0])
student=StudentModel(student_id=args.id, name=args.name, embedding=embedding)
crud.create_student(student)
print(f"Student {args.name} registered successfully")