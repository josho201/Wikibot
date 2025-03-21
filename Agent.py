from datetime import datetime
import gradio as gr
from openai import OpenAI
from dotenv import dotenv_values 
import re

from wikibot.tts import kokoro_text_to_speech   
from wikibot.utils import process_tool_calls
from wikibot.whisper import transcribe

config = dotenv_values(".env")

# Point to the local server
#client = OpenAI(api_key = config.get("OPENAI_API_KEY"))
client = OpenAI(base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",api_key = config.get("ALI_API_KEY"))
#client = OpenAI(base_url= "http://172.28.224.1:1234/v1", api_key="lm-studio")
#client = OpenAI(base_url="http://192.168.5.53:1234/v1", api_key="lm-studio")

model = "deepseek-r1-distill-llama-8b"
model = "gemma-3-12b-it"
model = "qwen2.5-7b-instruct"
model = "gpt-4o-mini"
model = "qwen-max"
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
                "required": ["search_query", "lan"],
            },
        },
    },
    {
    "type": "function",
    "function": {
        "name": "fetch_google_content",
        "description": (
            "Search the web using Google to retrieve the top results for a given query. "
            "This tool is useful when the user needs more information on a specific topic. "
            "If there is a typo in the query, it will be corrected before performing the search."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "search_query": {
                    "type": "string",
                    "description": "The search query to be used for finding relevant web results."
                }
            },
            "required": ["search_query"]
        }
    }
    },
    {
    "type": "function",
    "function": {
        "name": "save_file",
        "description": (
            "Creates a file locally with the specified name, extension, and content. "
            "This tool is useful for saving programs, summaries, research, or any other content as requested. "
            "It should be called only after the content to be saved has been generated."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The name of the file to be created, without the extension. If not provided, a default name will be chosen."
                },
                "content": {
                    "type": "string",
                    "description": "The content to be saved inside the file."
                },
                "extension": {
                    "type": "string",
                    "description": "The file extension (e.g., '.txt' for plain text, '.py' for Python, '.js' for JavaScript). If not specified, an appropriate extension will be chosen based on the content."
                }
            },
            "required": ["filename", "content", "extension"]
        }
    }
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": (
                "Opens the given URL and returns the content of the website. "
                "Use this with the most relevant URL provided by 'fetch_google_content' or a directly given URL. "
                "Feel free to use it with any provided URL to retrieve the content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the website to open."
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "solve_equation",
            "description": (
                "Solves a LaTeX equation by performing operations like differentiation, integration, simplification, etc. "
                "The LaTeX formula must clearly specify the operation to be performed. "
                "This tool is designed to perform these operations accurately."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "equation": {
                        "type": "string",
                        "description": "The equation or formula to solve, must be in LaTeX format without latex delimiters"
                    }
                },
                "required": ["equation"]
            }
        }
    }
]


current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')

messages = []

def clear_chat():
    global messages
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant capable of performing the following tasks: "
                "- Searching content on Google (fetch_google_content)"
                #" and Wikipedia (fetch_wikipedia_content)."       
                "- Fetching relevant information from websites using URLs (open_url). "
                "- Saving files with specific extensions (save_file). "
                "- Solving math problems (solve_equation). "
                "You can use multiple tools simultaneously. "
                "Do not hesitate to use these capabilities as much as possible to provide the best results. "
                "After using a tool to generate a solution, prioritize presenting the result directly. "
                "If the result is a mathematical answer or a factual statement, avoid unnecessary explanations or re-solving unless the user specifically asks for further steps or clarification. "
                "You are bilingual in English and Spanish. "
                f"The current date and time is: {current_date}"
                )
    }

    ]

    return messages

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
        clear_chat()
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
            messages.append(assistant_tool_call_message)
                    
            result = process_tool_calls(final_tool_calls, messages)
            
            for y in result:
                if type(y) is str:
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


def add_user_message(user_message, history):
    if user_message.strip() == "":
        return "", history
    # Append the user message to the chat history
    history.append({"role": "user", "content": user_message})
    return "", history



message = ""

def stream_response(history):

    global message
    inside_code_block = False
    buffer = ""
    latex_pattern = re.compile(r"\$\$(.*?)\$\$|\\\((.*?)\\\)|\\\[(.*?)\\\]")  # Remove LaTeX
    
    user_message = history[-1]['content']

    history.append({"role": "assistant", "content": ""})
    
    for new_chunk in chat(user_message, history):
        #print(new_chunk)
        history[-1]['content'] = new_chunk
        yield history

        message += new_chunk

        # print(message[-3:])    
        if "```" in message[-3:]:
            inside_code_block = not inside_code_block
            continue
        if not inside_code_block:
            buffer += new_chunk
            buffer = latex_pattern.sub("", buffer)  # Remove LaTeX
           # buffer = code_pattern.sub("", buffer)  # Remove code blocks

        #print(buffer)

        while match := re.search(r"([.!?:])\s+", buffer):
            sentence, buffer = buffer[:match.end()], buffer[match.end():]
            print("whole sentence: ", sentence.strip())


    if buffer.strip():
        print("whole sentence", buffer.strip())

transcription= ""

def print_transcription(a,b):
    print(transcription)

def process_audio(audio, history):
    global transcription
    chunk = transcribe(audio)
    transcription.join(chunk)
    print(chunk, flush=True)
    return
    speech_text = transcribe(audio)

    if speech_text.strip() == "":
        return "", history
    # Append the user message to the chat history
    history.append({"role": "user", "content": speech_text})
    return "", history
    
css = """
.message-row.bubble.bot-row.svelte-yaaj3 { max-width: 70% !important}
#submit {background-color: #04AA6D}
.col     {width: 20% !important}
"""

def say_output(history):
    return
    last_chatbot_message = history[-1]['content'].replace("\n", "")
    print(last_chatbot_message)

    audio = kokoro_text_to_speech(last_chatbot_message)   
    a,b = next(audio) 
    yield a,b

with gr.Blocks(css = css) as demo:  
    chatbot = gr.Chatbot(
        type="messages", 
        latex_delimiters = latex_delimiters_set,
        show_copy_button = True,
        #editable = "all",
        scale = 0
        )
    with gr.Row():

        audio = gr.Audio(
            sources=["microphone"], 
            type="filepath", 
            
            )
        
        msg = gr.Textbox(
            placeholder="Enter your message here"
            )
        
        with gr.Column(elem_classes="col"):
            submit = gr.Button(
                "Submit",
                elem_classes="btn", 
                elem_id="submit"
                )
            
            clear = gr.Button(
                "Clear", 
                elem_classes="btn"
                )
    
    with gr.Row():
        
        stream_btn = gr.Button('Stream', variant='primary')
        stop_btn = gr.Button('Stop', variant='stop')
        
        out_stream = gr.Audio(
            label='Output Audio Stream', 
            interactive=False, streaming=True, 
            autoplay=True
        )   

        #stream_event = stream_btn.click(fn=generate_all, inputs=[text], outputs=[out_stream], api_name=None)
        # stop_btn.click(fn=None, cancels=stream_event)

    
    audio.stream(
        process_audio, 
        inputs=[audio, chatbot],
        #stream_every=1.5
        )
    
    audio.stop_recording(
        print_transcription, 
        inputs=[audio, chatbot],
       
        )
    ##audio.stop_recording(process_audio, inputs=[audio, chatbot], outputs=[msg, chatbot])\
      ##  .then(stream_response, chatbot, chatbot, queue=True)
    
    # When the user submits a message, first update the conversation history.
    submit.click(add_user_message, inputs=[msg, chatbot], outputs=[msg, chatbot], queue=False)\
        .then(stream_response, chatbot, chatbot, queue=True)
    #    .then(say_output,inputs=[chatbot], outputs=[out_stream], api_name=None)
    
    # Clear button resets the chatbot history.
    clear.click(clear_chat , None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch(share=True)