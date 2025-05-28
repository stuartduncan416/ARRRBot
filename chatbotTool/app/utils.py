import time
from functools import wraps
from app import app

def benchmark(name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            app.logger.info(f"⏱️ {name} took {elapsed:.3f} seconds")
            return result
        return wrapper
    return decorator