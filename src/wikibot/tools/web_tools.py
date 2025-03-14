
import urllib.request
import urllib.parse

def fetch_wikipedia_content(search_query: str, lan: str = "en") -> dict:
    """
    Fetches Wikipedia content for a given search_query by first searching for
    the most relevant article and then retrieving a summary extract.
    """
    try:
        # Set API endpoint based on language
        if lan == "es":
            base_url = "https://es.wikipedia.org/w/api.php"
        else:
            base_url = "https://en.wikipedia.org/w/api.php"
        
        # Step 1: Search for the article using a less specific phrase
        search_params = {
            "format": "json",
            "action": "query",
            "list": "search",
            "srsearch": search_query,
            "utf8": 1,
        }
        search_url = f"{base_url}?{urllib.parse.urlencode(search_params)}"
        with urllib.request.urlopen(search_url) as response:
            search_data = json.loads(response.read().decode())
        
        search_results = search_data.get("query", {}).get("search", [])
        if not search_results:
            return {
                "status": "error",
                "message": f"No article found for '{search_query}'."
            }
        
        # Choose the first (most relevant) result
        first_result = search_results[0]
        pageid = first_result.get("pageid")
        title = first_result.get("title")
        
        # Step 2: Retrieve article extract using the page ID
        extract_params = {
            "format": "json",
            "action": "query",
            "prop": "extracts",
            "pageids": pageid,
            "explaintext": True,
           # "exchars": 2000,  # Specify the number of characters for the extract
            "utf8": 1,
            "redirects": 1
        }
        extract_url = f"{base_url}?{urllib.parse.urlencode(extract_params)}"
        print(extract_url)
        with urllib.request.urlopen(extract_url) as response:
            extract_data = json.loads(response.read().decode())
        
        page = extract_data.get("query", {}).get("pages", {}).get(str(pageid), {})
        content = page.get("extract", "")
        
        return {
            "status": "success",
            "title": title,
            "content": content
        }
    
    except Exception as e:
        print("error fetching wiki", e)
        return {"status": "error", "message": str(e)}