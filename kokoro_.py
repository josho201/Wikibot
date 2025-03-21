from kokoro import KModel, KPipeline
import gradio as gr
import torch
CHAR_LIMIT = 5000
kokoro_model = KModel().to('cuda').eval()
kokoro_pipeline = KPipeline(lang_code="a", model=False)

kokoro_pipeline.g2p.lexicon.golds['kokoro'] = 'kˈOkəɹO'

def forward_gpu(ps, ref_s, speed):
    return kokoro_model(ps, ref_s, speed)

def generate_all(text, voice='af_heart', speed=1.2, use_gpu=True):
    text = text if CHAR_LIMIT is None else text.strip()[:CHAR_LIMIT]
    pipeline = kokoro_pipeline
    pack = pipeline.load_voice(voice)
    first = True
    for _, ps, _ in pipeline(text, voice, speed):
        ref_s = pack[len(ps)-1]
        try:
            if use_gpu:
                audio = forward_gpu(ps, ref_s, speed)
            else:
                audio = kokoro_model(ps, ref_s, speed)
        except gr.exceptions.Error as e:
            if use_gpu:
                gr.Warning(str(e))
                gr.Info('Switching to CPU')
                audio = kokoro_model(ps, ref_s, speed)
            else:
                raise gr.Error(e)
        print(24000, audio.numpy())
        yield 24000, audio.numpy()
        if first:
            first = False
            print(24000, audio.numpy())
            yield 24000, torch.zeros(1).numpy()


def generate_first(
        text, 
        voice='af_heart',
        speed=1.2, 
        use_gpu=True
        ):
    
    text = text if CHAR_LIMIT is None else text.strip()[:CHAR_LIMIT]
    pipeline = kokoro_pipeline

    pack = pipeline.load_voice(voice)

    for _, ps, _ in pipeline(text, voice, speed):

        ref_s = pack[len(ps)-1]
        try:
            if use_gpu:
                audio = forward_gpu(ps, ref_s, speed)
            else:
                print("????????????????")
        except gr.exceptions.Error as e:
            if use_gpu:
                gr.Warning(str(e))
                gr.Info('Retrying with CPU. To avoid this error, change Hardware to CPU.')
                print("??????????????????????????????????")
            else:
                raise gr.Error(e)
        return (24000, audio.numpy()), ps
    return None, ''


with gr.Blocks() as demo:
    text = gr.Textbox(
        label='Input Text', 
        info=f"Up to ~500 characters per Generate, or {'∞' if CHAR_LIMIT is None else CHAR_LIMIT} characters per Stream"
        )
    
    out_ps = gr.Textbox(
        interactive=False,
        show_label=False, 
        info='Tokens used to generate the audio, up to 510 context length.'
        )
    
    out_audio = gr.Audio(
        label='Output Audio', 
        interactive=False, 
        streaming=False, 
        autoplay=True
        )
    
    
    generate_btn = gr.Button(
        'Generate', 
        variant='primary'
        )
    
    with gr.Row():
        stream_btn = gr.Button('Stream', variant='primary')
        stop_btn = gr.Button('Stop', variant='stop')
        out_stream = gr.Audio(
            label='Output Audio Stream', 
            interactive=False, streaming=True, 
            autoplay=True
        )

    stream_event = stream_btn.click(fn=generate_all, inputs=[text], outputs=[out_stream], api_name=None)
    stop_btn.click(fn=None, cancels=stream_event)


    generate_btn.click(
        fn=generate_first, 
        inputs=[text],
        outputs=[out_audio, out_ps], 
        api_name=None
        )

if __name__ == "__main__":
    demo.launch(share=True)