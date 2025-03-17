from datetime import datetime
from openai import OpenAI # type: ignore
import shutil
from wikibot.utils import process_tool_calls
import gradio as gr # type: ignore
    
# Point to the local server

client = OpenAI(base_url= "http://192.168.5.108:1234/v1", api_key="lm-studio")
#client = OpenAI(base_url="http://192.168.5.108:1234/v1", api_key="lm-studio")

model = "deepseek-r1-distill-llama-8b"
model = "gemma-3-12b-it"
model = "qwen2.5-7b-instruct"
tools = [

    { # fetch wikipedia content
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
                        "description": "Language tags for API. Currently supported: en,es, switch according to the user's language",
                    },
                },
                "required": ['search_query", "lan'],
            },
        },
    },
    { # fetch google content
    
        "type": "function",
        "function": {
            "name": "fetch_google_content",
            "description": (
            "Search the entire web with google and get top results. "
            "Use this if the user is asking for something very specific"
            "Use this when the user asks for more info on a specific topic"
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
                "required": ['search_query", "lan'],
            },
        },
    },
    { # save file
        "type": "function",
        "function": {
            "name": "save_file",
            "description": (
                "Creates a file locally with the especified name, extension, and content"
                "Useful for saving programs, summaries, research, or whatever is requested"
                "Call only after the content requested has been created"
                ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Name of the file to be created without extention, "
                        "if not provided, choose it",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to be saved inside the file.",
                    },
                    "extention": {
                        "type": "string",
                        "description": "the file extention, [dot].txt for plain text, [dot].py for python, [dot].js for javascript, etc."
                        "if isn´t specified, choose the most optimal for the case",
                    },
                },
                "required": ['filename","content", "extention'],
            },
        },
    },
    { # fetch URL content
        
            "type": "function",
            "function": {
                "name": "open_url",
                "description": (
                "Opens given URL and returns the content of the site."
                "use it with the most relevant URL given by fetch_google_content or with a given URL."
                "Dont hesitate to use it with a given url"
            ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL of the website to open",
                        },
                    },
                    "required": ['url", "lan'],
                },
            },
        },
    { # Solve 
    
        "type": "function",
        "function": {
            "name": "solve_ecuation",
            "description": (
                "Takes a latex operation and solves it."
                "Can solve differentiation, integration, simplification, etc."
                "The LaTeX formula MUST include the operation to be done."
                "This tool doesn't make mistakes"
        ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ecuation": {
                        "type": "string",
                        "description": "Ecuation or formula to solve, must be in LaTeX shape",
                    },
                },
                "required": ['ecuation']
            },
        },
    } 
    
]



messages = [
        {
            "role": "system",
            "content": 
            "You are a helpful assistant who can search content on google and wikipedia, "
            "you can also save files with specific extensions. "
            "You can use multiple tools at once."
            "Use these capabilities whenever posible to provide the best and most reliable results."
           # "Hablas Español e Ingles "
            f"the current date is {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}",
        }
    ]

latex_delimiters_set = [
        {"left": "$$", "right": "$$", "display": True},
        {"left": "\\(", "right": "\\)", "display": False},
        { "left": '\\[', "right": '\\]', "display": True},
        #{"left": "$", "right": "$", "display": False},
    ]


def chat(user_input, history):
    global messages  # Ensure we persist conversation history
    
    if user_input.lower() == "msg":
        yield "Printing..."
        print(messages)  # Show the entire conversation history
        return
    if user_input.lower() == "clr":
        yield "resetting"
        messages = [
        {
            "role": "system",
            "content": 
            ("You are a helpful assistant that can search content on google (fetch_google_content) and wikipedia (fetch_wikipedia_content),"
            "You can fetch URL's to get relevant information from within websites (open_url)"
            "You save files with specific extensions. (save_file)"
            "You can solve math problems. (solve_ecuation)"
            "You can use multiple tools at once."
            "Do not hesitate to use these capabilities as much as posible to provide the best posible results."
            "After using a tool to generate a solution, prioritize presenting that result directly. "
            "If the result is a mathematical answer or a factual statement, "
            "avoid unnecessary explanation or re-solving unless the user specifically asks for further steps or clarification."
           # "Hablas Español e Ingles "
           f"the current date is { datetime.now().strftime('%Y-%m-%d%H:%M:%S %Z') }"
          )
        }
    ]
        return
    
    # Append user message to conversation history
    messages.append({"role": "user", "content": user_input})
    
    try:
        # Get initial response from model
        stream = client.chat.completions.create(
            model=model,
            messages=messages,  # Use the updated messages list
            tools=tools,
            stream=True
        )
        
        final_tool_calls = {}
        assistant_msgs = ""

        for chunk in stream:
            if chunk.choices[0].delta.tool_calls:
                for tool_call in chunk.choices[0].delta.tool_calls or []:
                    index = tool_call.index
                    if index not in final_tool_calls:
                        final_tool_calls[index] = tool_call
                    else:
                        final_tool_calls[index].function.arguments += tool_call.function.arguments
            else:
                if chunk.choices[0].delta.content is not None:
                    
                    assistant_msgs += chunk.choices[0].delta.content
                    yield assistant_msgs
        
        

        tool_meta = ""          
        # If tool calls are present, process them and continue the conversation
        if final_tool_calls:
            result = process_tool_calls(final_tool_calls, messages)
            
            for y in result:
                print(y, " --- ", type(y))  

                if type(y) is str:
                    print(y, "AJAAA ")
                    assistant_msgs += str(y) + "\n"
                    tool_meta = y
                    yield assistant_msgs
                elif y is dict:
                    messages.append(y)

            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    
                    assistant_msgs += chunk.choices[0].delta.content
                    yield assistant_msgs

        # Save final assistant response
        messages.append({"role": "assistant", "content": assistant_msgs, "metadata": {'title': tool_meta}})

    except Exception as e:
        print(f"Error: {e}")



def clear_chat():
    global messages
    messages = [
        {
            "role": "system",
            "content": 
            "You are a helpful assistant who can search content on google and wikipedia, "
            "you can also save files with specific extensions. "
            "You can use multiple tools at once."
            "Use these capabilities whenever posible to provide the best and most reliable results."
           # "Hablas Español e Ingles "
            f"the current date is {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}",
        }
    ]

    return messages

def add_user_message(user_message, history):
    if user_message.strip() == "":
        return "", history
    # Append the user message to the chat history
    history.append({"role": "user", "content": user_message})
    return "", history

def stream_response(history):
    # Extract the last user message
    user_message = history[-1]['content']
    
    # The assistant's response will be streamed from your chat() function.
    # Initially, we add an empty assistant message to the history.
    history.append({"role": "assistant", "content": ""})
    
    # Stream the response and update the assistant message in history.
    # Yield the full conversation after each update.
    for new_chunk in chat(user_message, history):
        # Update the last assistant message with the new streaming chunk.
        history[-1]['content'] = new_chunk
        yield history

with gr.Blocks(css = ".message-row.bubble.bot-row.svelte-yaaj3 { max-width: 70% !important}") as demo:
    chatbot = gr.Chatbot(
        type="messages", 
        latex_delimiters = latex_delimiters_set,
        show_copy_button = True,
        editable = "all",
        scale = 0
        )
    msg = gr.Textbox(placeholder="Enter your message here")
    clear = gr.Button("Clear")
    
    # When the user submits a message, first update the conversation history.
    msg.submit(add_user_message, inputs=[msg, chatbot], outputs=[msg, chatbot], queue=False)\
       .then(stream_response, chatbot, chatbot, queue=True)
    
    # Clear button resets the chatbot history.
    clear.click(clear_chat      , None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch()