from transformers import WhisperProcessor, WhisperForConditionalGeneration
 # type: ignore
from torch.nn.attention import SDPBackend, sdpa_kernel # type: ignore
from transformers import BitsAndBytesConfig
import torch # type: ignore
import time

from torch import float16, compile, inference_mode  # type: ignore
from torchaudio import load as load_audio # type: ignore
from torchaudio.transforms import Resample # type: ignore


quant_config= BitsAndBytesConfig(
    load_in_8bit=True,  # Use 8-bit quantization
    bnb_8bit_compute_dtype= float16,
    bnb_8bit_use_double_quant=True
)

# load model and processor
start = time.perf_counter()
print("loading whisper ...")
whisper_path = "./whisper-small"
processor = WhisperProcessor.from_pretrained(whisper_path)



model = WhisperForConditionalGeneration.from_pretrained(
    whisper_path,  
    #torch_dtype=torch.float16,
    quantization_config=quant_config, 
    device_map = "cuda"
    )

print("Whisper succesfully loaded")

model = compile(model)
model.config.forced_decoder_ids = None
end = time.perf_counter()
print(f"Time taken: {end - start:.6f} seconds")


# Load local audio file
audio_path = "audio/test.mp3"


def transcribe(audio):
    start = time.perf_counter()
    # Load audio and preprocess
   ## print("loading audio")
    waveform, sample_rate = load_audio(audio)

    ##print("resampling audio")
    resampler = Resample(orig_freq=sample_rate, new_freq=16000)
    waveform = resampler(waveform)
    
    # Move input features to GPU and convert to float16 for efficiency
    ##print("processing audio")
    input_features = processor(
        waveform.squeeze().numpy(), 
        sampling_rate=16000, 
        return_tensors="pt"
        ).input_features
    input_features = input_features.to("cuda").half()

    # Generate transcription
    
    ##print("generating transcription")

    with inference_mode():
        predicted_ids = model.generate(input_features)

    #print("decoding transcription")    
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
    end = time.perf_counter()
    #print(f"Time taken: {end - start:.6f} seconds")
    #print("optimizing resources and exporting transcription")
    del waveform, resampler, input_features,predicted_ids
    torch.cuda.empty_cache()
    return transcription[0]


