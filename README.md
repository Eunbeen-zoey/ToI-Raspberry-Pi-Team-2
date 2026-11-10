# ToI-Raspberry-Pi-Team-2

## 블록 형식
| 필드 | 설명 | 예시 |
|---|---|---|
| index | 블록 번호 | 1 |
| timestamp | 생성 시각(초) | 1731200000.12 |
| type | genesis / issue / transfer / use | "issue" |
| data | 거래 내용 | {"ticket_id":"T1","from":null,"to":"user1","price":50000} |
| prev_hash | 앞 블록의 hash | "a3f9..." |
| hash | 이 블록의 SHA-256 | "b773..." |

## 유저: user1(최은빈), user2(홍서연), user3(최승희)
## 공연: show1, 정가 50000원

## API
- POST /buy      {user_id, show_id}             → {ok, ticket_id}
- POST /transfer {ticket_id, from, to, price}   → {ok, reason}
- POST /enter    {user_id}                      → {ok, reason}
