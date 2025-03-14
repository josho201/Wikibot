import webbrowser
import os

def is_valid_url(url: str) -> bool:

    try:
        result = urlparse(url)
        return bool(result.netloc)  # Returns True if there's a valid network location
    except Exception:
        return False


def open_safe_url(url: str) -> dict:
    # List of allowed domains (expand as needed)
    SAFE_DOMAINS = {
        "lmstudio.ai",
        "github.com",
        "google.com",
        "wikipedia.org",
        "weather.com",
        "stackoverflow.com",
        "python.org",
        "x.com",    
        "docs.python.org",
    }

    try:
        # Add http:// if no scheme is present
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        # Validate URL format
        if not is_valid_url(url):
            return {"status": "error", "message": f"Invalid URL format: {url}"}

        # Parse the URL and check domain
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        base_domain = ".".join(domain.split(".")[-2:])

        if base_domain in SAFE_DOMAINS:
            print("oppening ", url)
            webbrowser.open(url)
            return {"status": "success", "message": f"Opened {url} in browser"}
        else:
            return {
                "status": "error",
                "message": f"Domain {domain} not in allowed list",
            }
    except Exception as e:
         return {"status": "error", "message": str(e)}


def get_current_time() -> dict:
    """Get the current system time with timezone information"""
    try:
        current_time = datetime.now()
        timezone = datetime.now().astimezone().tzinfo
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        return {
            "status": "success",
            "time": formatted_time,
            "timezone": str(timezone),
            "timestamp": current_time.timestamp(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}




def analyze_directory(path: str = ".") -> dict:
    """Count and categorize files in a directory"""
    try:
        stats = {
            "total_files": 0,
            "total_dirs": 0,
            "file_types": {},
            "total_size_bytes": 0,
        }

        for entry in os.scandir(path):
            if entry.is_file():
                stats["total_files"] += 1
                ext = os.path.splitext(entry.name)[1].lower() or "no_extension"
                stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
                stats["total_size_bytes"] += entry.stat().st_size
            elif entry.is_dir():
                stats["total_dirs"] += 1
                # Add size of directory contents
                for root, _, files in os.walk(entry.path):
                    for file in files:
                        try:
                            stats["total_size_bytes"] += os.path.getsize(os.path.join(root, file))
                        except (OSError, FileNotFoundError):
                            continue

        return {"status": "success", "stats": stats, "path": os.path.abspath(path)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
