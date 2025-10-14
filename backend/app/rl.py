
import redis, os, time
_pool=None
def redis_client(url=None):
    global _pool
    if _pool is None:
        _pool = redis.from_url(url or os.getenv("REDIS_URL","redis://localhost:6379/0"), decode_responses=True)
    return _pool
def token_bucket(key, capacity:int, refill_rate:float):
    r=redis_client(); now=time.time()
    st=r.hgetall(key) or {}
    tokens=float(st.get("tokens", capacity)); last=float(st.get("ts", now))
    tokens=min(capacity, tokens+(now-last)*refill_rate)
    if tokens<1.0:
        r.hset(key, mapping={"tokens":tokens,"ts":now}); r.expire(key,60)
        wait=max(1,int((1.0-tokens)/refill_rate)); return False, wait
    tokens-=1.0; r.hset(key, mapping={"tokens":tokens,"ts":now}); r.expire(key,60)
    return True, 0
