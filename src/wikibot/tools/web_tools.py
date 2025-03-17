import json
import urllib.request
import urllib.parse
import requests # type: ignore
from bs4 import BeautifulSoup # type: ignore
import re
from dotenv import load_dotenv
import os

load_dotenv()


def extract_content(
        url,
        unwanted_classes:list = ["social", "share", "follow", "ads", "popup", "widget", "related", "sidebar", "menu"],
        unwanted_tags:list = ["header", "footer", "nav", "aside", "script", "style", "button", "svg"],
        wanted_tags:list = ["h1", "h2", "h3","p", "li", "span", "pre"],
        headers:object = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"    
            }   
        ):
   
    # Build regex pattern from array
    unwanted_regex = re.compile(r"|".join(unwanted_classes), re.IGNORECASE)
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove unwanted sections (header, footer, nav, etc.)
        for tag in soup(unwanted_tags):
            tag.decompose()

        # Remove unwanted classes     
        for tag in soup.find_all(class_=lambda c: c and unwanted_regex.search(c)):
            tag.decompose()
        
        paragraphs = []

        for p in soup.find_all(wanted_tags):
            content = p.get_text()
            if(p.name == "h1"):
                content = f"tittle: {p.get_text()}."
            elif (p.name == "h2"):
                content = f"sub-tittle: {p.get_text()}."
            elif (p.name == "h3"):
                content = f"subsection-tittle: {p.get_text()}."
            elif (p.name == "li"):
                content = f"-{p.get_text()}."
            elif (p.name == "p"):
                content = f" {p.get_text()}. "
            paragraphs.append(content)
        return "".join(paragraphs)  # Return first 5 paragraphs as relevant content
    
    return "Failed to fetch content."

def fetch_wikipedia_content(search_query: str, lan: str = "en") -> dict:
    """
    Fetches Wikipedia content for a given search_query by first searching for
    the most relevant article and then retrieving a summary extract.
    """
    try:
        # Set API endpoint based on language
        base_url = f"https://{lan}.wikipedia.org/w/api.php"
        
        
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
        content = str(page.get("extract", "")).replace("\n", '').replace("\t","")
        
        page_url = f"https://{lan}.wikipedia.org/w/index.php?curid={pageid}"
        
        return {
            "status": "success",
            "title": title,
            "content": content,
            "url": page_url
        }
    
    except Exception as e:
        print("error fetching wiki", e)
        return {"status": "error", "message": str(e)}
    
def fetch_google_search_results(
        search_query: str, 
        api_key: str = os.getenv('GOOGLE_API_KEY'), 
        cx: str = os.getenv('GOOGLE_CX')
        ) -> dict:
    """
    Fetches search results from Google Custom Search API for a given search_query.
    
    Parameters:
        search_query: The search phrase.
        api_key: Your Google API key.
        cx: The custom search engine ID.
    
    Returns:
        A dictionary with the status and either a list of result items or an error message.
    """
    try:
        google_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cx,
            "q": search_query,
        }
        url = f"{google_url}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url) as response:
            search_data = json.loads(response.read().decode())
        
        if "items" not in search_data:
            return {"status": "error", "message": "No search results found."}
        
        results = []
        for item in search_data['items']:
            results.append({
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "link": item.get("link")
            })
        
        return {
            "status": "success",
            "results": results
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}