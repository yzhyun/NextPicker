import asyncio
import time
from typing import Any, Optional, Dict
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class SimpleCache:
    def __init__(self, ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            item = self.cache[key]
            if time.time() - item['timestamp'] < self.ttl:
                return item['value']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def clear(self) -> None:
        self.cache.clear()
    
    def size(self) -> int:
        return len(self.cache)

# 전역 캐시 인스턴스
cache = SimpleCache()

def cached(ttl: Optional[int] = None):
    """함수 결과를 캐시하는 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # 캐시에서 확인
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 결과 캐시
            cache.set(cache_key, result)
            logger.debug(f"Cache miss for {cache_key}, stored result")
            
            return result
        return wrapper
    return decorator

async def cached_async(ttl: Optional[int] = None):
    """비동기 함수 결과를 캐시하는 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # 캐시에서 확인
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # 함수 실행
            result = await func(*args, **kwargs)
            
            # 결과 캐시
            cache.set(cache_key, result)
            logger.debug(f"Cache miss for {cache_key}, stored result")
            
            return result
        return wrapper
    return decorator
