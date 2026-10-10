"""Optional expiring invitation gate for the hosted review deployment.

Normal local/BYO-key runs do not enable this middleware. The invitation token is
loaded from the host environment, never stored in Git or logged in URLs.
"""

import hmac
import os
import time
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse, JSONResponse

COOKIE = "argand_review"
LOGIN = """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Argand · Private review</title>
<style>body{font:17px/1.6 system-ui;background:#f5f9f9;color:#243d3b;max-width:520px;margin:15vh auto;padding:24px}h1{font-size:30px}p{color:#536a66}</style>
<h1>Argand</h1><p id="message">This demo is available by private invitation for a limited review period. Open the invitation link supplied with your application.</p>
<script>
(async()=>{const token=new URLSearchParams(location.hash.slice(1)).get('invite');
if(!token)return;
history.replaceState(null,'',location.pathname);
const response=await fetch('/api/review/access',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token})});
if(response.ok)location.replace('/');
else document.querySelector('#message').textContent='This invitation is invalid or the review period has ended.';
})().catch(()=>document.querySelector('#message').textContent='The review could not be opened. Please try again.');
</script></html>"""


def public_origin():
    return os.getenv("ARGAND_PUBLIC_ORIGIN", "").rstrip("/")


class ReviewAccess(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        origin = public_origin()
        if not origin:
            return await call_next(request)

        token = os.getenv("ARGAND_REVIEW_TOKEN", "")
        try:
            expires = int(os.getenv("ARGAND_REVIEW_EXPIRES", "0"))
        except ValueError:
            expires = 0
        if len(token) < 32 or expires <= time.time():
            return HTMLResponse(
                "<h1>This review demo has closed.</h1>",
                status_code=410,
                headers={"Cache-Control": "no-store"},
            )

        if request.url.hostname != urlparse(origin).hostname:
            return JSONResponse({"detail": "Unexpected review host"}, status_code=403)
        if (
            request.method not in ("GET", "HEAD")
            and request.headers.get("origin") != origin
        ):
            return JSONResponse(
                {"detail": "Unexpected request origin"}, status_code=403
            )

        if request.url.path == "/api/review/access" and request.method == "POST":
            body = await request.body()
            if len(body) > 1024:
                return JSONResponse({"detail": "Invalid invitation"}, status_code=400)
            try:
                import json

                supplied = json.loads(body).get("token", "")
            except (ValueError, AttributeError):
                supplied = ""
            if not isinstance(supplied, str) or not hmac.compare_digest(
                supplied.encode(), token.encode()
            ):
                return JSONResponse({"detail": "Invalid invitation"}, status_code=403)
            response = JSONResponse({"ok": True})
            response.set_cookie(
                COOKIE,
                token,
                max_age=max(0, int(expires - time.time())),
                secure=True,
                httponly=True,
                samesite="strict",
            )
        elif not hmac.compare_digest(
            request.cookies.get(COOKIE, "").encode(), token.encode()
        ):
            response = (
                JSONResponse(
                    {"detail": "A private review invitation is required"},
                    status_code=401,
                )
                if request.url.path.startswith("/api/")
                else HTMLResponse(LOGIN, status_code=401)
            )
        else:
            response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response
