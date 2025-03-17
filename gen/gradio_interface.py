import gradio as gr

def greet(name):
    return f"Hello, {name}!"

# Create the Gradio interface
iface = gr.Interface(fn=greet, inputs="text", outputs="text")

# Launch the interface
iface.launch()