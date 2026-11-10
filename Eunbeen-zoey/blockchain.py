import hashlib # SHA-256 해시 계산을 위해 hashlib 모듈을 사용
import json # # 데이터를 JSON 형식으로 바꾸고 되돌리기 위해 json 모듈을 사용
import os # 파일 존재 여부 확인을 위해 os 모듈을 사용
import time # 타임스탬프를 위해 time 모듈을 사용

CHAIN_FILE = "chain.json"


class Block:
    def __init__(self, index, timestamp, type, data, prev_hash, hash=None):
        self.index = index
        self.timestamp = timestamp
        self.type = type
        self.data = data
        self.prev_hash = prev_hash
        # hash를 넘기면(파일에서 불러올 때) 그대로 쓰고, 없으면 새로 계산
        self.hash = hash if hash is not None else self.calc_hash()

    def calc_hash(self):
        content = {
            "index": self.index,
            "timestamp": self.timestamp,
            "type": self.type,
            "data": self.data,
            "prev_hash": self.prev_hash,
        }
        text = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "type": self.type,
            "data": self.data,
            "prev_hash": self.prev_hash,
            "hash": self.hash,
        }

    @staticmethod
    def from_dict(d):
        return Block(d["index"], d["timestamp"], d["type"], d["data"],
                     d["prev_hash"], d["hash"])


class Blockchain:
    def __init__(self, filename=CHAIN_FILE):
        self.filename = filename
        self.chain = []
        if os.path.exists(self.filename):
            self.load()
        else:
            self.chain.append(self.create_genesis())
            self.save()

    def create_genesis(self):
        return Block(0, time.time(), "genesis", {}, "0")

    def last_block(self):
        return self.chain[-1]

    def add_block(self, type, data):
        prev = self.last_block()
        block = Block(prev.index + 1, time.time(), type, data, prev.hash)
        self.chain.append(block)
        self.save()
        return block

    def is_valid(self):
        for i, block in enumerate(self.chain):
            # ① 내용 조작 확인
            if block.hash != block.calc_hash():
                return False, f"{i}번 블록 내용이 조작됨"
            # ② 연결 확인
            if i > 0 and block.prev_hash != self.chain[i - 1].hash:
                return False, f"{i}번 블록과 {i-1}번 블록 연결이 끊어짐"
        return True, "정상"

    def save(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump([b.to_dict() for b in self.chain], f,
                      ensure_ascii=False, indent=2)

    def load(self):
        with open(self.filename, "r", encoding="utf-8") as f:
            self.chain = [Block.from_dict(d) for d in json.load(f)]


if __name__ == "__main__":
    bc = Blockchain()
    if len(bc.chain) == 1:
        bc.add_block("issue", {"ticket_id": "T1", "from": None, "to": "user1", "price": 50000})
        bc.add_block("transfer", {"ticket_id": "T1", "from": "user1", "to": "user2", "price": 50000})
    for b in bc.chain:
        print(b.index, b.type, b.data, b.hash[:10])
    ok, msg = bc.is_valid()
    print("검증 결과:", msg)