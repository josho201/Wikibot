from datetime import datetime
from openai import OpenAI # type: ignore
import shutil
from wikibot.utils import process_tool_calls

# Point to the local server
client = OpenAI(base_url="http://192.168.5.108:1234/v1/", api_key="lm-studio")
model = "qwen2.5-7b-instruct-1m"

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
                "required": ["url", "lan"],
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
                    "lan": {
                        "type": "string",
                        "description": "Language tags for API. Currently supported: en,es",
                    },
                },
                "required": ["search_query"],
            },
        },
    }
]


def chat():
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that can open safe web links, "
            "tell the current time, and analyze directory contents. "
            "Hablas Español e Ingles "
            "You can use multiple tools at once. Use these capabilities whenever they might be helpful."
            f"the current date is {datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")}",
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
        elif user_input.lower() == "clear":
            print("Conversation Reset...")
            print("-"*shutil.get_terminal_size().columns)
            print(
            "Assistant: Hello! I can help you open safe web links, "
            "tell you the current time, and analyze directory contents. "
            "What would you like me to do?"
            )
            messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that can open safe web links, tell the current time, and analyze directory contents. You can use multiple tools at once. don't hesitate about these capabilities whenever they might be helpful.",
            }
            ]   
            continue
        elif(user_input.lower() == "msg"):
            print(messages)
            continue


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

            assistant_msgs = ""

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
                    if chunk.choices[0].delta.content is not None:
                        print(chunk.choices[0].delta.content, end="", flush=True)
                        assistant_msgs +=  chunk.choices[0].delta.content
                    
            
                        

            if len(final_tool_calls):      
                #print("tool calling success... ")   
                messages = process_tool_calls(final_tool_calls, messages)
                stream = client.chat.completions.create(
                model=model,
                messages=messages,
                stream = True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        print(chunk.choices[0].delta.content, end="", flush=True)
                        assistant_msgs +=  chunk.choices[0].delta.content

        

            # Add user message to conversation
            messages.append({"role": "assistant", "content": assistant_msgs})
             
            

        except Exception as e:
            print(e)

if __name__ == "__main__":
    chat()