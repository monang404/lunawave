from core.constants import MAX_RATE_LIMIT


async def check_rate_limit(manager, client_ip: str, now: float) -> bool:
    async with manager.rl_lock:
        cmd_history = manager.command_history.get(client_ip, [])
        cmd_history = [t for t in cmd_history if now - t < 60]
        if not cmd_history:
            manager.command_history.pop(client_ip, None)
        else:
            manager.command_history[client_ip] = cmd_history
        if len(cmd_history) >= MAX_RATE_LIMIT:
            return False
        cmd_history.append(now)
        manager.command_history[client_ip] = cmd_history
        return True

from aiohttp import web

@web.middleware
async def security_headers_middleware(request, handler):
    response = await handler(request)
    
    # Konfigurasi HTTP security headers
    response.headers.setdefault('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://i.ytimg.com; connect-src 'self' ws: wss:;")
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    
    return response
