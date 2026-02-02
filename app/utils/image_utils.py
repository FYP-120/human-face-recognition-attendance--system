import cv2
def read_image(path):
    return cv2.imread(path)

def rsize_face(face_img, size=(160,160)):
    return cv2.resize(face_img,size)