import requests
import logging
import time
from utils import getHeader

logger = logging.getLogger(__name__)

_SITEMATRIX_CACHE = {
    "expires_at": 0,
    "projects": set(),
    "languages": set(),
}

CACHE_TTL_SECONDS = 3600

def _fetch_sitematrix():
    """Fetch SiteMatrix data from Wikimedia API and populate cache."""
    try:
        sitematrix_url = "https://meta.wikimedia.org/w/api.php?action=sitematrix&format=json"
        response = requests.get(sitematrix_url, headers=getHeader(), timeout=30)
        response.raise_for_status()
        data = response.json()
        
        projects = set()
        languages = set()
        sitematrix = data.get("sitematrix", {})
        
        for key, val in sitematrix.items():
            if key == "count":
                continue
            
            if key == "specials":
                if isinstance(val, list):
                    for site in val:
                        if site.get("closed"):
                            continue
                        site_url = site.get("url")
                        if site_url:
                            normalized_url = normalize_project(site_url)
                            if normalized_url:
                                projects.add(normalized_url)
                continue
            
            if isinstance(val, dict):
                lang_code = val.get("code")
                if lang_code:
                    languages.add(lang_code.lower())
                
                sites = val.get("site", [])
                for site in sites:
                    if site.get("closed"):
                        continue
                    site_url = site.get("url")
                    if site_url:
                        normalized_url = normalize_project(site_url)
                        if normalized_url:
                            projects.add(normalized_url)
        
        _SITEMATRIX_CACHE["projects"] = projects
        _SITEMATRIX_CACHE["languages"] = languages
        _SITEMATRIX_CACHE["expires_at"] = time.time() + CACHE_TTL_SECONDS
        
        logger.info(f"SiteMatrix cache updated: {len(projects)} projects, {len(languages)} languages")
        return True
        
    except Exception as e:
        logger.error(f"Failed to fetch SiteMatrix: {e}")
        return False


def _ensure_cache():
    """Ensure cache is populated and fresh."""
    if time.time() > _SITEMATRIX_CACHE["expires_at"]:
        return _fetch_sitematrix()
    return True


def normalize_project(project):
    """Normalize project URL to match SiteMatrix format."""
    if not project:
        return None
    
    normalized = project.strip().lower()
    normalized = normalized.replace("https://", "").replace("http://", "")
    normalized = normalized.rstrip("/")
    
    return normalized


def normalize_language_code(language_code):
    """Normalize language code."""
    if not language_code:
        return None
    return language_code.strip().lower()


def is_valid_project(project):
    """Check if a project exists in Wikimedia SiteMatrix."""
    if not project:
        return False
    
    normalized = normalize_project(project)
    
    if not _ensure_cache():
        logger.warning("SiteMatrix cache unavailable, allowing project (fail-open)")
        return True
    
    return normalized in _SITEMATRIX_CACHE["projects"]


def is_valid_language(language_code):
    """Check if a language code exists in Wikimedia SiteMatrix."""
    if not language_code:
        return False
    
    normalized = normalize_language_code(language_code)
    
    if not _ensure_cache():
        logger.warning("SiteMatrix cache unavailable, allowing language (fail-open)")
        return True
    
    return normalized in _SITEMATRIX_CACHE["languages"]


def get_cached_projects():
    """Get list of valid projects (for debugging/admin endpoints)."""
    _ensure_cache()
    return sorted(_SITEMATRIX_CACHE["projects"])


def get_cached_languages():
    """Get list of valid languages (for debugging/admin endpoints)."""
    _ensure_cache()
    return sorted(_SITEMATRIX_CACHE["languages"])
