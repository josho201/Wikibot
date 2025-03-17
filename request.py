import requests
from bs4 import BeautifulSoup
import re

def extract_content(url):

    # List of class keywords to remove
    unwanted_classes = ['social", "share", "follow", "ads", "popup", "widget", "related", "sidebar']
     # Build regex pattern from array
    unwanted_regex = re.compile(r"|".join(unwanted_classes), re.IGNORECASE)

    # List of html tags to delete
    unwated_tags = ['header", "footer", "nav", "aside", "script", "style", "button']

    wanted_tags = ['h1", "h2", "h3","p", "li", "span", "pre", "shreddit-post",  "shreddit-title", "shreddit-app']


    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove unwanted sections (header, footer, nav, etc.)
        for tag in soup(unwated_tags):
            tag.decompose()

        # Remove unwanted classes     
        for tag in soup.find_all(class_=lambda c: c and unwanted_regex.search(c)):
            tag.decompose()

        paragraphs = [p.get_text().replace('\n', "").replace("\t", "").replace("  ","") for p in soup.find_all(wanted_tags)]
        return "".join(paragraphs)  # Return first 5 paragraphs as relevant content
    
    return "Failed to fetch content."

# Example usag

url = "https://www.crummy.com/software/BeautifulSoup/bs4/doc/#calling-a-tag-is-like-calling-find-all"
url = "https://www.reddit.com/r/nvidia/comments/lskbdp/geforce_rtx_3060_review_megathread/"
print(extract_content(url))
