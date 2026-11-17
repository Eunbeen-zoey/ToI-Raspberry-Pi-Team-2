
import cv2
import json
from pathlib import Path


# ====================================
# 1. 파일 경로 설정
# ====================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "face_model.yml"
LABEL_PATH = BASE_DIR / "label_map.json"
CASCADE_PATH = BASE_DIR / "haarcascade_frontalface_default.xml"


# ====================================
# 2. 모델 및 파일 불러오기
# ====================================

if not MODEL_PATH.exists():
    raise FileNotFoundError("face_model.yml 파일이 없습니다.")

if not LABEL_PATH.exists():
    raise FileNotFoundError("label_map.json 파일이 없습니다.")

if not CASCADE_PATH.exists():
    raise FileNotFoundError("haarcascade_frontalface_default.xml 파일이 없습니다.")

# LBPH 얼굴인식 모델
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(str(MODEL_PATH))

# 얼굴 검출기
cascade = cv2.CascadeClassifier(str(CASCADE_PATH))

if cascade.empty():
    raise RuntimeError("얼굴 검출기 파일을 읽을 수 없습니다.")

# 사용자 ID 불러오기
with open(LABEL_PATH, "r", encoding="utf-8") as f:
    label_map = json.load(f)

label_map = {
    int(key): value
    for key, value in label_map.items()
}

# 미등록자 판별 기준
# 초기 테스트값이며 실제 테스트 결과에 따라 조정해야 함
UNKNOWN_THRESHOLD = 70.0


# ====================================
# 3. 얼굴인식 함수
# ====================================

def recognize(frame):
    """
    카메라 프레임을 입력받아 사용자 ID를 반환한다.

    등록된 사람: "user1", "user2", "user3"
    미등록자 또는 얼굴 미검출: None
    """

    if frame is None:
        return None

    # 컬러 이미지를 흑백으로 변환
    if len(frame.shape) == 2:
        gray = frame
    else:
        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

    # 얼굴 위치 찾기
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(100, 100)
    )

    # 얼굴이 검출되지 않으면 None 반환
    if len(faces) == 0:
        return None

    # 가장 큰 얼굴 선택
    x, y, w, h = max(
        faces,
        key=lambda face: face[2] * face[3]
    )

    # 얼굴 영역 자르기
    face = gray[y:y+h, x:x+w]

    # 크기 통일
    face = cv2.resize(face, (200, 200))

    # 학습 모델과 비교
    label, confidence = recognizer.predict(face)

    # 숫자 라벨을 사용자 ID로 변환
    user_id = label_map.get(int(label))

    # 등록되지 않은 사용자 판별
    if user_id is None or confidence > UNKNOWN_THRESHOLD:
        return None

    # 정상 인식 시 사용자 ID 반환
    return user_id


# ====================================
# 4. 카메라 테스트
# ====================================

if __name__ == "__main__":

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("카메라 연결 실패")
        raise SystemExit

    print("얼굴인식 시작!")
    print("Q를 누르면 종료합니다.")

    last_user_id = "START"

    while True:

        ret, frame = camera.read()

        if not ret:
            print("카메라 화면을 가져오지 못했습니다.")
            break

        # 실제 얼굴인식 함수 호출
        user_id = recognize(frame)

        # 얼굴 검출 위치를 별도로 표시
        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        faces = cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100)
        )

        if len(faces) > 0:

            x, y, w, h = max(
                faces,
                key=lambda face: face[2] * face[3]
            )

            if user_id is not None:
                message = user_id
                box_color = (0, 255, 0)
            else:
                message = "Unknown"
                box_color = (0, 0, 255)

            cv2.rectangle(
                frame,
                (x, y),
                (x+w, y+h),
                box_color,
                2
            )

        else:
            message = "No Face Detected"

        # 카메라 화면에 결과 표시
        cv2.putText(
            frame,
            message,
            (10, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        # CMD에는 결과가 바뀔 때만 출력
        if user_id != last_user_id:
            print("인식 결과:", user_id)
            last_user_id = user_id

        cv2.imshow(
            "Face Recognition",
            frame
        )

        # Q를 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()

    print("얼굴인식 종료!")
