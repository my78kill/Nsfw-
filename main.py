from fastapi import FastAPI, File, UploadFile, Header, HTTPException
import shutil
from nudenet import NudeClassifier
import cv2
import os

app = FastAPI()
classifier = NudeClassifier()

API_KEY = "sk_92KjsH@8sKx_91!dkL"   # 👈 apni strong key rakhna

# -------- SECURITY CHECK --------
def verify_key(x_api_key):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")


# -------- IMAGE CHECK --------
def check_image(path):
    result = classifier.classify(path)
    return result[path]['unsafe'] > 0.7


# -------- VIDEO CHECK --------
def check_video(path):
    cap = cv2.VideoCapture(path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % max(fps,1) == 0:
            temp = "frame.jpg"
            cv2.imwrite(temp, frame)

            result = classifier.classify(temp)
            if result[temp]['unsafe'] > 0.7:
                return True

        frame_count += 1

    return False


# -------- API ROUTE --------
@app.post("/check")
async def check(file: UploadFile = File(...), x_api_key: str = Header(None)):

    verify_key(x_api_key)  # 🔐 check key

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
