
import cv2
import numpy as np
import json
from pathlib import Path

# 현재 train.py가 있는 폴더
BASE_DIR = Path(__file__).resolve().parent

# 사진이 저장된 폴더
DATASET_DIR = BASE_DIR / "dataset"

# 학습 결과 저장 위치
MODEL_PATH = BASE_DIR / "face_model.yml"
LABEL_PATH = BASE_DIR / "label_map.json"


# 얼굴 학습 함수
def train_model():

    faces = []
    labels = []
    label_map = {}

    # dataset 폴더가 있는지 확인
    if not DATASET_DIR.exists():
        print("dataset 폴더가 없습니다.")
        return

    # user1, user2, user3 폴더 찾기
    user_dirs = sorted(
        p for p in DATASET_DIR.iterdir()
        if p.is_dir()
    )

    if not user_dirs:
        print("사용자 사진 폴더가 없습니다.")
        return

    # 사용자별 사진 읽기
    for label, user_dir in enumerate(user_dirs):

        user_id = user_dir.name

        # 사용자 번호와 이름 연결
        label_map[str(label)] = user_id

        image_paths = sorted(user_dir.glob("*.jpg"))

        if not image_paths:
            print(user_id + "의 사진이 없습니다.")
            return

        count = 0

        for image_path in image_paths:

            # 사진 불러오기
            image = cv2.imread(
                str(image_path),
                cv2.IMREAD_GRAYSCALE
            )

            if image is None:
                print("사진 읽기 실패:", image_path)
                continue

            # 모든 사진 크기를 통일
            image = cv2.resize(image, (200, 200))

            # 얼굴 사진과 사용자 번호 저장
            faces.append(image)
            labels.append(label)

            count += 1

        if count == 0:
            print(user_id + "의 사진을 읽을 수 없습니다.")
            return

        print(user_id, "사진", count, "장 확인")

    # LBPH 학습 시작
    recognizer = cv2.face.LBPHFaceRecognizer_create()

    recognizer.train(
        faces,
        np.array(labels, dtype=np.int32)
    )

    # 학습 결과 저장
    recognizer.save(str(MODEL_PATH))

    # 사용자 번호 정보 저장
    with open(LABEL_PATH, "w", encoding="utf-8") as f:
        json.dump(
            label_map,
            f,
            ensure_ascii=False,
            indent=4
        )

    print("----------------------")
    print("얼굴 학습 완료!")
    print("총 학습 사진:", len(faces))
    print("학습 모델 저장 완료!")
    print("사용자 정보 저장 완료!")


# 프로그램 실행
if __name__ == "__main__":
    train_model()
