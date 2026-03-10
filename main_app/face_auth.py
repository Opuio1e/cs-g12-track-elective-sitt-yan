import base64

FACE_VECTOR_SIZE = 64


def _load_cv_libs():
    try:
        import cv2
        import numpy as np
    except Exception as exc:
        raise ValueError("Face recognition dependencies are missing. Install numpy and opencv-python-headless.") from exc
    return cv2, np


def image_data_to_bgr(image_data):
    cv2, np = _load_cv_libs()

    if not image_data:
        raise ValueError("Capture a photo first.")

    if "," in image_data:
        image_data = image_data.split(",", 1)[1]

    try:
        raw_bytes = base64.b64decode(image_data)
    except Exception as exc:
        raise ValueError("Invalid photo data.") from exc

    np_buffer = np.frombuffer(raw_bytes, dtype=np.uint8)
    image = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image.")

    return image


def _get_face_detector():
    cv2, _ = _load_cv_libs()
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    if detector.empty():
        raise ValueError("Face detector could not be loaded.")
    return detector


def extract_face_embedding(image_bgr):
    cv2, np = _load_cv_libs()
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    detector = _get_face_detector()
    faces = detector.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(70, 70))
    if len(faces) == 0:
        raise ValueError("No clear face found. Center your face and try again.")

    x, y, w, h = max(faces, key=lambda box: box[2] * box[3])
    face = gray[y:y + h, x:x + w]
    face = cv2.resize(face, (FACE_VECTOR_SIZE, FACE_VECTOR_SIZE), interpolation=cv2.INTER_AREA)
    face = cv2.equalizeHist(face)

    vector = face.astype(np.float32).reshape(-1) / 255.0
    vector = vector - np.mean(vector)
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError("Face capture quality is too low. Try better lighting.")

    normalized = vector / norm
    return normalized.tolist()


def cosine_similarity(first_vector, second_vector):
    _, np = _load_cv_libs()
    first = np.asarray(first_vector, dtype=np.float32)
    second = np.asarray(second_vector, dtype=np.float32)

    if first.shape != second.shape:
        return -1.0

    denominator = np.linalg.norm(first) * np.linalg.norm(second)
    if denominator == 0:
        return -1.0

    return float(np.dot(first, second) / denominator)
