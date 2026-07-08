import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, limit: int = 10, period: int = 60, gc_interval: int = 60):
        self.limit = limit
        self.period = period
        self.gc_interval = gc_interval
        self.clients = defaultdict(list)
        self.last_gc = time.monotonic()
    
    def _gc(self, now: float):
        if now - self.last_gc > self.gc_interval:
            stale_ips = [ip for ip, hist in self.clients.items() if not any(now - t < self.period for t in hist)]
            for ip in stale_ips:
                self.clients.pop(ip, None)
            self.last_gc = now

    def is_allowed(self, client_id: str) -> bool:
        now = time.monotonic()
        self._gc(now)
        
        requests = self.clients[client_id]
        
        # Remove old requests
        requests = [req for req in requests if now - req < self.period]
        self.clients[client_id] = requests
        
        if len(requests) >= self.limit:
            return False
        
        requests.append(now)
        return True

global_rate_limiter = RateLimiter(limit=20, period=60, gc_interval=60)
