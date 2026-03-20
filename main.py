import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # force CPU

from fastapi import FastAPI, File, UploadFile, Header, HTTPException
import shutil
import cv2
from nudenet import NudeDetector

app = FastAPI()

# 🔐 API KEY
API_KEY = "mysecret123"

# 🧠 MODEL (ONNX based)
detector = NudeDetector()


# -------- SECURITY --------
def verify_key(x_api_key):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")


# -------- IMAGE CHECK --------
def check_image(path):
    result = detector.detect(path)

    for item in result:
        if item['score'] > 0.6:
            return True

    return False


# -------- VIDEO CHECK --------
def check_video(path):
    cap = cv2.VideoCapture(path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # har 1 sec ka frame
        if frame_count % max(fps, 1) == 0:
            temp = "frame.jpg"
            cv2.imwrite(temp, frame)

            result = detector.detect(temp)

            for item in result:
                if item['score'] > 0.6:
                    return True

        frame_count += 1

    cap.release()
    return False


# -------- API ROUTE --------
@app.post("/check")
async def check(file: UploadFile = File(...), x_api_key: str = Header(None)):

    verify_key(x_api_key)

    path = file.filename

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    ext = path.split('.')[-1].lower()

    if ext in ["jpg", "jpeg", "png", "webp"]:
        result = check_image(path)
    else:
        result = check_video(path)

    os.remove(path)

    return {"nsfw": result}
