from insightface.app import FaceAnalysis
import numpy as np


app=FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

def get_embedding(face_image):
    """
    Get embedding from face image
    Args:
        face_image: numpy array of the face image (RGB format)
    Returns:
        List of embedding values or None if no face detected
    """
    # Ensure the image has the right shape and type
    if not isinstance(face_image, np.ndarray):
        return None
    
    # InsightFace expects BGR format
    if len(face_image.shape) == 3 and face_image.shape[2] == 3:
        # Convert RGB to BGR for insightface
        face_image_bgr = face_image[:, :, ::-1].copy()
    else:
        return None
    
    faces=app.get(face_image_bgr)
    if len(faces)==0:
        return None
    return faces[0].embedding.tolist()


def get_all_embeddings(face_image):
    """
    Get embeddings for ALL detected faces in the image
    Args:
        face_image: numpy array of the face image (RGB format)
    Returns:
        List of tuples (embedding, bbox) or empty list if no faces detected
        bbox format: [x, y, x2, y2] coordinates
    """
    # Ensure the image has the right shape and type
    if not isinstance(face_image, np.ndarray):
        return []
    
    # InsightFace expects BGR format
    if len(face_image.shape) == 3 and face_image.shape[2] == 3:
        # Convert RGB to BGR for insightface
        face_image_bgr = face_image[:, :, ::-1].copy()
    else:
        return []
    
    faces = app.get(face_image_bgr)
    if len(faces) == 0:
        return []
    
    # Return embeddings with bounding boxes for all detected faces
    results = []
    for face in faces:
        embedding = face.embedding.tolist()
        bbox = face.bbox.tolist()  # [x, y, x2, y2]
        results.append((embedding, bbox))
    
    return results

