import redis
import json
import os

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True
)

def get_messages(session_id):
    key = f"chat:{session_id}"
    data = r.get(key)
    return json.loads(data) if data else []

def append_message(session_id, role, content):
    key = f"chat:{session_id}"
    history = get_messages(session_id)
    history.append({"role": role, "content": content})
    # 최근 20개까지만 유지
    if len(history) > 20:
        history = history[-20:]
    r.set(key, json.dumps(history), ex=60 * 60 * 6)  # TTL 6시간
