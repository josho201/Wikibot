import json
from urllib.parse import urlparse
import webbrowser
from datetime import datetime
import os
from openai import OpenAI

import urllib.parse

import shutil
import urllib.request

# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
model = "qwen2.5-7b-instruct-1m"


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


def fetch_wikipedia_content(search_query: str) -> dict:
    """Fetches wikipedia content for a given search_query"""
    try:
        # Search for most relevant article
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            
            "format": "json",
            "action": "query",
            "prop": "extracts",
            "generator": "search",
            ""
            "gsrinterwiki": True,
            "gsrsearch": search_query,
            "gsrenablerewrites": False,
            "exintro":True,
            "exlimit": "max",
            "explaintext": True,
            "exsentences": 10
        }
        """
        https://en.wikipedia.org/w/api.php?
            format=json&
            action=query&
            prop=extracts&
            generator=search&
            gsrsearch=types%20of%20transistor&
            exlimit=max&
        """
        url = f"{search_url}?{urllib.parse.urlencode(search_params)}"
        
        with urllib.request.urlopen(url) as response:
            search_data = json.loads(response.read().decode())
        

        pages = search_data["query"]["pages"]

        if not len(pages):
            return {
                "status": "errror",
                "message": f"No Wikipedia article found for '{search_query}'",
            }
        
        keys = pages.keys()
        content = ""
        for key in keys:
            content += pages[key]["title"] + "\n"
            content += pages[key]["extract"] + "\n"

       
        return {
            "status": "success",
            "content": content,
            "title": search_query,
        }


        

    except Exception as e:
        print("error fetching wiki", e)
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


tools = [
    {
        "type": "function",
        "function": {
            "name": "open_safe_url",
            "description": "Open a URL in the browser if it's deemed safe",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to open",
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current system time with timezone information",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_directory",
            "description": "Analyze the contents of a directory, counting files and folders",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory path to analyze. Defaults to current directory if not specified.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_wikipedia_content",
            "description": (
            "Search Wikipedia and fetch the extract of the article with the best match for the query. "
            "Always use this if the user is asking for something that is most likely on wikipedia"
            "Use this when the user asks for more info on a specific topic"
            "Use this when the information the user is asking for is unclear"
            "If the user has a typo in their search query, correct it before searching."
        ),
            "parameters": {
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": "Search query for finding the Wikipedia article.",
                    },
                },
                "required": ["search_query"],
            },
        },
    }
]


def process_tool_calls(final_tool_calls, messages):
    

    # Create the assistant message with tool calls
    assistant_tool_call_message = {
        "role": "assistant",
        "tool_calls": [
            {
                "id": final_tool_calls[key].id,
                "type": final_tool_calls[key].type,
                "function": {
                    "arguments": final_tool_calls[key].function.arguments,
                    "name": final_tool_calls[key].function.name,
                },
            }
            for key in final_tool_calls.keys()
        ],
    }

    # print( "_ assistant_tool_call_message:  ",assistant_tool_call_message)

    tool_results = []
    for tool_call in assistant_tool_call_message["tool_calls"]:
        arguments = json.loads(tool_call["function"]["arguments"])
        name = tool_call["function"]["name"]

        # Determine which function to call based on the tool call name
        if name == "open_safe_url":
            result = open_safe_url(arguments["url"])

        elif name == "get_current_time":
            result = get_current_time()

        elif name == "analyze_directory":
            path = arguments.get("path", ".")
            result = analyze_directory(path)

        elif name == "fetch_wikipedia_content":

            search_query = arguments["search_query"]
            print(f"Looking for {search_query} on wikipedia... ")
            result = fetch_wikipedia_content(search_query)
            terminal_width = shutil.get_terminal_size().columns
            #print("\n" + "=" * terminal_width)
        
            if result["status"] == "success":
                print(f"Found results for {search_query} at {result['title']}")
                """
                print(f"\nWikipedia article: {result['title']}")
                print("-" * terminal_width)
                print(result["content"])
                """
            else:
                print(
                f"\nError fetching content: {result['message']}"
                )
        
            
        else:
            # llm tried to call a function that doesn't exist, skip
            continue

        # Add the result message
        tool_result_message = {
            "role": "tool",
            "content": json.dumps(result),
            "tool_call_id": tool_call["id"],
        }
        tool_results.append(tool_result_message)
        messages.append(tool_result_message)
    

    return messages
    

def chat():
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that can open safe web links, tell the current time, and analyze directory contents. You can use multiple tools at once. Use these capabilities whenever they might be helpful.",
        }
    ]

    print(
        "Assistant: Hello! I can help you open safe web links, tell you the current time, and analyze directory contents. What would you like me to do?"
    )
    print("(Type 'quit' to exit)")

    while True:
        # Get user input
        user_input = input("\nYou: ").strip()

        # Check for quit command
        if user_input.lower() == "quit":
            print("Assistant: Goodbye!")
            break

        # Add user message to conversation
        messages.append({"role": "user", "content": user_input})

        try:
            # Get initial response
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                stream = True
            )
            
            
            final_tool_calls = {}

            for chunk in stream:
                if chunk.choices[0].delta.tool_calls:
                    #print("calling tools .... ")
                    for tool_call in chunk.choices[0].delta.tool_calls or []:
                        index = tool_call.index

                        if index not in final_tool_calls:
                            final_tool_calls[index] = tool_call

                        final_tool_calls[index].function.arguments += tool_call.function.arguments
                else:
                    #print("No tools to be called ... ")
                    print(chunk.choices[0].delta.content, end="", flush=True)
                    
            
                        

            if len(final_tool_calls):      
                #print("tool calling success... ")   
                messages = process_tool_calls(final_tool_calls, messages)
                stream = client.chat.completions.create(
                model=model,
                messages=messages,
                stream = True
                )
                for chunk in stream:
                    print(chunk.choices[0].delta.content, end="", flush=True)
                    

        

                    
            

        except Exception as e:
            print(e)

if __name__ == "__main__":
    chat()