from binascii import Error
from kokoro import KModel, KPipeline
import torch

CHAR_LIMIT = 5000
kokoro_model = KModel().to('cuda').eval()
kokoro_pipeline = KPipeline(lang_code="a", model=False)

kokoro_pipeline.g2p.lexicon.golds['kokoro'] = 'kˈOkəɹO'

def kokoro_text_to_speech(text, voice='af_heart', speed=1.2, use_gpu=True):
    #text = text if CHAR_LIMIT is None else text.strip()[:CHAR_LIMIT]
    pipeline = kokoro_pipeline
    pack = pipeline.load_voice(voice)
    first = True
    for _, ps, _ in pipeline(text, voice, speed):
        ref_s = pack[len(ps)-1]

        try:
            if use_gpu:
                audio = kokoro_model(ps, ref_s, speed)
        except Exception as e:
                raise Error(e)
        
        yield 24000, audio.numpy()
        if first:
            first = False
            yield 24000, torch.zeros(1).numpy()