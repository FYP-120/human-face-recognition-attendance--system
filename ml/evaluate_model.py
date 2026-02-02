import numpy as np
from sklearn.metrics import accuracy_score
from app.services.face_matcher import cosine_similarity

EMBEDDINGS_FILE = "datasets/embeddings/student_embeddings.npy"
THRESHOLD = 0.6

def evaluate():
    data = np.load(EMBEDDINGS_FILE, allow_pickle=True).item()
    student_ids = data["student_ids"]
    embeddings = data["embeddings"]

    y_true = []
    y_pred = []

    for i in range(len(embeddings)):
        best_score = 0
        best_match = None

        for j in range(len(embeddings)):
            if i == j:
                continue
            score = cosine_similarity(embeddings[i], embeddings[j])
            if score > best_score:
                best_score = score
                best_match = student_ids[j]

        y_true.append(student_ids[i])
        y_pred.append(best_match if best_score > THRESHOLD else "unknown")

    accuracy = accuracy_score(y_true, y_pred)
    print(f"Model Accuracy: {accuracy * 100:.2f}%")

if __name__ == "__main__":
    evaluate()
