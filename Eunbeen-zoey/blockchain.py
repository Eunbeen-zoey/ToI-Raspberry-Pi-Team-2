import hashlib  # SHA-256 해시 계산
import json     # 데이터를 JSON 형식으로 바꾸고 되돌리기
import os       # 파일 존재 여부 확인
import time     # 타임스탬프

CHAIN_FILE = "chain.json"

# 회의에서 정한 유저와 공연 정보
USERS = ["user1", "user2", "user3"]
SHOWS = {
    "show1": {"name": "스마트티켓 콘서트", "price": 50000},
}


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

    # ---------- 2주차: 조회 함수 ----------

    def get_ticket_blocks(self, ticket_id):
        """이 티켓과 관련된 블록만 순서대로 모아서 돌려줌"""
        return [b for b in self.chain if b.data.get("ticket_id") == ticket_id]

    def get_owner(self, ticket_id):
        """티켓의 현재 주인 (없는 티켓이면 None)"""
        owner = None
        for b in self.get_ticket_blocks(ticket_id):
            if b.type in ("issue", "transfer"):
                owner = b.data["to"]
        return owner

    def is_used(self, ticket_id):
        """이미 입장에 사용된 티켓인지"""
        for b in self.get_ticket_blocks(ticket_id):
            if b.type == "use":
                return True
        return False

    def get_ticket_price(self, ticket_id):
        """티켓의 정가 (발급 블록에 적힌 가격)"""
        for b in self.get_ticket_blocks(ticket_id):
            if b.type == "issue":
                return b.data["price"]
        return None

    def get_all_tickets(self):
        """발급된 모든 티켓 ID 목록"""
        return [b.data["ticket_id"] for b in self.chain if b.type == "issue"]

    def find_ticket(self, user_id):
        """이 유저가 가진, 아직 안 쓴 티켓 ID (없으면 None)"""
        for ticket_id in self.get_all_tickets():
            if self.get_owner(ticket_id) == user_id and not self.is_used(ticket_id):
                return ticket_id
        return None

    # ---------- 2주차: 거래 함수 ----------

    def issue_ticket(self, user_id, show_id):
        """발급(예매). 성공: (True, 티켓ID) / 실패: (False, 이유)"""
        ok, msg = self.is_valid()
        if not ok:
            return False, "체인 위변조 감지: " + msg
        if user_id not in USERS:
            return False, "등록되지 않은 유저"
        if show_id not in SHOWS:
            return False, "없는 공연"

        ticket_id = "T" + str(len(self.get_all_tickets()) + 1)
        self.add_block("issue", {
            "ticket_id": ticket_id,
            "show_id": show_id,
            "from": None,
            "to": user_id,
            "price": SHOWS[show_id]["price"],
        })
        return True, ticket_id

    def transfer_ticket(self, ticket_id, from_user, to_user, price):
        """양도. 성공: (True, 메시지) / 실패: (False, 이유)"""
        ok, msg = self.is_valid()
        if not ok:
            return False, "체인 위변조 감지: " + msg

        try:
            price = int(price)   # 웹 폼에서 문자열로 와도 숫자로 바꿈
        except (TypeError, ValueError):
            return False, "가격이 숫자가 아님"

        owner = self.get_owner(ticket_id)
        if owner is None:
            return False, "없는 티켓"
        if owner != from_user:
            return False, "티켓 주인이 아님"
        if self.is_used(ticket_id):
            return False, "이미 사용된 티켓"
        if to_user not in USERS:
            return False, "받는 사람이 등록되지 않은 유저"
        if to_user == from_user:
            return False, "자기 자신에게 양도할 수 없음"
        if price < 0:
            return False, "가격이 잘못됨"
        if price > self.get_ticket_price(ticket_id):
            return False, "정가 초과 양도 불가"

        self.add_block("transfer", {
            "ticket_id": ticket_id,
            "from": from_user,
            "to": to_user,
            "price": price,
        })
        return True, "양도 완료"

    def use_ticket(self, user_id):
        """입장(사용). 성공: (True, 메시지) / 실패: (False, 이유)"""
        ok, msg = self.is_valid()
        if not ok:
            return False, "체인 위변조 감지: " + msg
        if user_id not in USERS:
            return False, "미등록자"

        ticket_id = self.find_ticket(user_id)
        if ticket_id is None:
            return False, "사용 가능한 티켓 없음"

        self.add_block("use", {
            "ticket_id": ticket_id,
            "from": user_id,
            "to": None,
            "price": 0,
        })
        return True, f"입장 허용 ({ticket_id})"


if __name__ == "__main__":
    # 매번 깨끗하게 테스트하려고 기존 chain.json을 지우고 시작
    if os.path.exists(CHAIN_FILE):
        os.remove(CHAIN_FILE)
    bc = Blockchain()

    print("1. user1 예매:", bc.issue_ticket("user1", "show1"))
    print("2. user1→user2 70000원 양도:", bc.transfer_ticket("T1", "user1", "user2", 70000))
    print("3. user1→user2 50000원 양도:", bc.transfer_ticket("T1", "user1", "user2", 50000))
    print("   T1 현재 주인:", bc.get_owner("T1"))
    print("4. user1 입장:", bc.use_ticket("user1"))
    print("5. user2 입장:", bc.use_ticket("user2"))
    print("6. user2 다시 입장:", bc.use_ticket("user2"))
    print("7. 미등록자 입장:", bc.use_ticket("unknown"))
    print("8. 사용된 티켓 양도:", bc.transfer_ticket("T1", "user2", "user3", 10000))

    print("\n--- 블록 목록 ---")
    for b in bc.chain:
        print(b.index, b.type, b.data)
    print("검증 결과:", bc.is_valid()[1])