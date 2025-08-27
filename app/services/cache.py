import hashlib
import json
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path


class DocumentCache:
    """Simple file-based cache for document analysis results."""
    
    def __init__(self, cache_dir: str = "cache", max_age_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.max_age_seconds = max_age_hours * 3600
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, content: bytes, filename: str) -> str:
        """Generate a unique cache key for document content."""
        content_hash = hashlib.md5(content).hexdigest()
        filename_hash = hashlib.md5(filename.encode()).hexdigest()
        return f"{content_hash}_{filename_hash}"
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the full path for a cache file."""
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, content: bytes, filename: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached analysis results."""
        try:
            cache_key = self._get_cache_key(content, filename)
            cache_path = self._get_cache_path(cache_key)
            
            if not cache_path.exists():
                return None
            
            # Check if cache is expired
            if time.time() - cache_path.stat().st_mtime > self.max_age_seconds:
                cache_path.unlink()
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                return cached_data
                
        except Exception:
            return None
    
    def set(self, content: bytes, filename: str, data: Dict[str, Any]) -> None:
        """Store analysis results in cache."""
        try:
            cache_key = self._get_cache_key(content, filename)
            cache_path = self._get_cache_path(cache_key)
            
            cache_data = {
                'timestamp': time.time(),
                'filename': filename,
                'data': data
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception:
            pass  # Silently fail if caching fails
    
    def clear_expired(self) -> int:
        """Remove expired cache entries and return count of removed files."""
        removed_count = 0
        current_time = time.time()
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                if current_time - cache_file.stat().st_mtime > self.max_age_seconds:
                    cache_file.unlink()
                    removed_count += 1
        except Exception:
            pass
        
        return removed_count
    
    def clear_all(self) -> int:
        """Remove all cache files and return count of removed files."""
        removed_count = 0
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                removed_count += 1
        except Exception:
            pass
        
        return removed_count
