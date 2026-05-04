from __future__ import annotations

from typing import Mapping, Optional
from urllib.parse import urlparse, urlunparse

import httpx


_PROXY_SCHEME_ALIASES = {
    "sock5": "socks5",
    "sock5h": "socks5h",
}
_SUPPORTED_PROXY_SCHEMES = frozenset({"http", "https", "socks5", "socks5h"})


def normalize_proxy_url(raw_proxy: Optional[str]) -> Optional[str]:
    """规范化代理地址。

    支持：
    - http://host:port
    - https://host:port
    - socks5://host:port
    - socks5h://host:port

    兼容用户常见写法：
    - sock5://... → socks5://...
    - sock5h://... → socks5h://...
    """
    if not isinstance(raw_proxy, str):
        return None
    proxy = raw_proxy.strip()
    if not proxy:
        return None

    parsed = urlparse(proxy)
    scheme = (parsed.scheme or "").strip().lower()
    if not scheme:
        return None
    scheme = _PROXY_SCHEME_ALIASES.get(scheme, scheme)
    if scheme not in _SUPPORTED_PROXY_SCHEMES:
        return None
    if not parsed.netloc:
        return None

    return urlunparse(
        (
            scheme,
            parsed.netloc,
            parsed.path or "",
            parsed.params or "",
            parsed.query or "",
            parsed.fragment or "",
        )
    )


def create_async_http_client(
    *,
    headers: Optional[Mapping[str, str]] = None,
    timeout_sec: float = 15.0,
    follow_redirects: bool = True,
    proxy: Optional[str] = None,
) -> httpx.AsyncClient:
    """创建插件内部使用的异步 HTTP 客户端。

    仅用于插件的“非模型提供商”请求，避免污染 AstrBot 全局网络配置。
    """
    timeout = max(2.0, float(timeout_sec))
    normalized_proxy = normalize_proxy_url(proxy)
    return httpx.AsyncClient(
        headers=dict(headers or {}),
        timeout=httpx.Timeout(timeout),
        follow_redirects=follow_redirects,
        proxy=normalized_proxy,
        trust_env=False,
    )
