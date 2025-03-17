from wikibot.tools.local_tools import open_safe_url,  get_current_time, analyze_directory, save_to_file, solve_eq
from wikibot.tools.web_tools import fetch_wikipedia_content, fetch_google_search_results, extract_content
import json


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
    for tool_call in assistant_tool_call_message['tool_calls']:
        arguments = json.loads(tool_call['function']['arguments'])
        name = tool_call['function']['name']

        # Determine which function to call based on the tool call name
        if name == "open_safe_url":
            result = open_safe_url(arguments['url'])

        elif name == "get_current_time":
            result = get_current_time()

        elif name == "analyze_directory":
            path = arguments.get("path", ".")
            result = analyze_directory(path)

        elif name == "fetch_wikipedia_content":
            lan = arguments['lan']
            search_query = arguments['search_query']
            yield f"Looking for {search_query} on wikipedia... "
            
            result = fetch_wikipedia_content(search_query, lan)
        
            if result['status'] == "success":
                yield f"Found results for {search_query} at <a href='{result['url']}'> {result['title']} </a>"
                
            else:
                yield f"\nError fetching content: {result['message']}"
                
        elif name == "fetch_google_content":
            search_query = arguments['search_query']

            yield f"Looking for '{search_query}' in Google..."
            result = fetch_google_search_results(search_query, api_key = "AIzaSyAl_gIfxN8GoHKmuD8EwLhhclv8ozm0yeI", cx="7484bf1a990da4dad")
            
        elif name == "save_file":
            yield  f"Creating file {arguments['filename']}{arguments['extention']}..."
            result = save_to_file(
                filename = arguments['filename'],
                content = arguments['content'],
                extention = arguments['extention']
                )
            yield  f"File {arguments['filename']}{arguments['extention']} saved."

        elif name == 'open_url':
            yield f"Going deeper into {arguments['url']}"
            result = extract_content(arguments['url'])           
        elif name == "solve_ecuation":
            yield f"Solving: \\({arguments['ecuation']} \\)"
            result = solve_eq(arguments['ecuation'])
           # yield f"Result: \\({result} \\)"
        else:
            # llm tried to call a function that doesn't exist, skip
            yield f"'{name}'tool not found ..."  


        # Add the result message
        tool_result_message = {
            "role": "tool",
            "content": json.dumps(result),
            "tool_call_id": tool_call['id'],
        }
        tool_results.append(tool_result_message)
        messages.append(tool_result_message)
    

    yield tool_result_message
    
    
