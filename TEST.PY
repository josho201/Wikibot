import re
streaming_text_v2 = """
    The formula for the distance between two points \((x_1, y_1)\) and \((x_2, y_2)\) in a Cartesian plane is given by: 
    \[d = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2} \] I have also created a Python function that implements this formula. 
    Here is the code: ```python import math def distance_between_points(x1, y1, x2, y2): 
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2) # Example usage: # d = distance_between_points(1, 2, 3, 4) 
    # print(d) ``` The code has been saved in a file named `distance_between_points.py`. 
    You can use this function by importing it into your Python script and passing the coordinates of the two points.
    """

message = ""

def stream_sentence_splitter_v5(text_stream):
    global message
    inside_code_block = False
    buffer = ""
    
    latex_pattern = re.compile(r"\$\$(.*?)\$\$|\\\((.*?)\\\)|\\\[(.*?)\\\]")  # Remove LaTeX
    
    sentence = ""
    for chunk in text_stream:   
        message += chunk

        # print(message[-3:])    
        if "```" in message[-3:]:
            inside_code_block = not inside_code_block
            continue
        if not inside_code_block:
            buffer += chunk
            buffer = latex_pattern.sub("", buffer)  # Remove LaTeX
           # buffer = code_pattern.sub("", buffer)  # Remove code blocks
        print(buffer)
        #if "." in chunk and not inside_code_block:

        while match := re.search(r"([.!?:])\s+", buffer):
            sentence, buffer = buffer[:match.end()], buffer[match.end():]
            yield sentence.strip()


    if buffer.strip():
        yield buffer.strip()



# Running the improved version
streamed_sentences_v5 = list(stream_sentence_splitter_v5(streaming_text_v2))
print(streamed_sentences_v5)