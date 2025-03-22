from wikibot.rag.tools import WikiFile
from openai import OpenAI
import gradio as gr
import dotenv
# Load the OpenAI API key from an environment variable
env = dotenv.dotenv_values()
openai_api_key = env['OPENAI_API_KEY']

#init openai
client = OpenAI(api_key= openai_api_key)
model = "gpt-4o-mini"
tools = [{
            "type":"function",
            "function":{
                "name":"RAG Query",
                "description":"Query the RAG model with a question and context",
                "parameters":{
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Keywords to include in the query"
                        }
                    }
                }
            }
    }]

#init wikifile
doc = WikiFile("testpdf/transformers.pdf")
doc.init()

messages = [{
            "role": "system",
            "content": 
            "You are an expert in transformers. You can access the paper 'Attention is All You Need' to help answer questions."
            "Via the RAG model, you can query the paper with keywords according to the users question."
        }]


def process_RAG(tool_calls):
    for tool_call in tool_calls.values():
        if tool_call.function.name == "RAG Query":
            question = tool_call.function.arguments["question"]
            
            content = doc.query(question)
            return {
                "role": "assistant",
                "content": content
            }    

def chat(user_input, history):
   # global messages  # Ensure we persist conversation history
    
    # Append user message to conversation history
    history.append({"role": "user", "content": user_input})
    
    try:
        # Get initial response from model
        stream = client.chat.completions.create(
            model=model,
            messages=history,  # Use the updated messages list
            tools=tools,
            stream=True
        )
        
        final_tool_calls = {}
        assistant_msgs = ""
       
        for chunk in stream:

            # If tool calls are present, process them and continue the conversation
            if chunk.choices[0].delta.tool_calls:

                for tool_call in chunk.choices[0].delta.tool_calls or []:
                    index = tool_call.index

                    if index not in final_tool_calls:
                        final_tool_calls[index] = tool_call
                    else:
                        final_tool_calls[index].function.arguments += tool_call.function.arguments

            # If assistant response is present, append it to the assistant message
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

            history.append(assistant_tool_call_message)
                    
            results = process_RAG(final_tool_calls, history)
            
            for result in results:
                history.append(result)

            # Get response from model after processing tool calls
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )
            # Yield assistant messages
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    assistant_msgs += chunk.choices[0].delta.content
                    yield assistant_msgs

    except Exception as e:
        print(f"Error: {e}")




latex_delimiters_set = [
        {"left": "$$", "right": "$$", "display": True},
        {"left": "\\(", "right": "\\)", "display": False},
        { "left": '\\[', "right": '\\]', "display": True},
        #{"left": "$", "right": "$", "display": False},
    ]

with gr.Blocks() as demo:  
    chatbot = gr.Chatbot(
        type="messages", 
        latex_delimiters = latex_delimiters_set,
        show_copy_button = True,
        #editable = "all",
        scale = 0
        )
    
    msg = gr.Textbox(
        placeholder="Enter your message here"
        )
    
    msg.submit(chat, [msg, chatbot], chatbot, queue=False)

demo.launch()