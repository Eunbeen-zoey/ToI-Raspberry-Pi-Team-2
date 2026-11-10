
import cv2
from pathlib import Path
import sys

# 1. 사용자 ID 입력
if len(sys.argv) < 2:
    print("사용법: python capture.py user1")
    sys.exit()

user_id = sys.argv[1]

# 2. 사진 저장 폴더 만들기
save_dir = Path("dataset") / user_id
save_dir.mkdir(parents=True, exist_ok=True)

count = len(list(save_dir.glob("*.jpg")))

# 3. 얼굴 찾기 기능 준비
cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)

if cascade.empty():
    print("얼굴 검출기 파일을 찾을 수 없습니다.")
    sys.exit()

# 4. 카메라 실행
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("카메라 연결 실패")
    sys.exit()

print("S: 사진 저장 / Q: 종료")

# 5. 얼굴 촬영 시작
while count < 30:

    ret, frame = camera.read()

    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(100, 100)
    )

    face_box = None

    if len(faces) > 0:

        x, y, w, h = max(
            faces,
            key=lambda f: f[2] * f[3]
        )

        face_box = (x, y, w, h)

        cv2.rectangle(
            frame,
            (x, y),
            (x+w, y+h),
            (0, 255, 0),
            2
        )

    cv2.putText(
        frame,
        f"Saved: {count}/30",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.imshow("Face Capture", frame)

    key = cv2.waitKey(1) & 0xFF

    # S를 누르면 사진 저장
    if key == ord('s'):

        if face_box is not None:

            x, y, w, h = face_box

            face = gray[y:y+h, x:x+w]

            face = cv2.resize(face, (200, 200))

            count += 1

            filename = save_dir / f"{count:03d}.jpg"

            cv2.imwrite(str(filename), face)

            print(f"사진 저장: {count}/30")

        else:
            print("얼굴을 찾지 못했습니다.")

    # Q를 누르면 종료
    elif key == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()

print("촬영 종료!")
print("저장된 사진:", count)
