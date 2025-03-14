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
            lan = arguments["lan"]
            search_query = arguments["search_query"]
            print(f"Looking for {search_query} on wikipedia... ")
            result = fetch_wikipedia_content(search_query, lan)
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
    
