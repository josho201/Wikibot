from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torchaudio # type: ignore
from transformers import BitsAndBytesConfig
import torch

quant_config= BitsAndBytesConfig(
    load_in_4bit=True,  # Use 8-bit quantization
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True
)

# load model and processor
processor = WhisperProcessor.from_pretrained("../whisper-small")

model = WhisperForConditionalGeneration.from_pretrained(
    "../whisper-small",  
    quantization_config=quant_config, 
    device_map = "cuda")

model.config.forced_decoder_ids = None


# Load local audio file
audio_path = "audio/test.mp3"



def transcribe(audio):
    # Load audio and preprocess
    waveform, sample_rate = torchaudio.load(audio)
    resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
    waveform = resampler(waveform)
    
    # Move input features to GPU and convert to float16 for efficiency
    input_features = processor(waveform.squeeze().numpy(), sampling_rate=16000, return_tensors="pt").input_features
    input_features = input_features.to("cuda").half()

    # Generate transcription
    predicted_ids = model.generate(input_features)
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
    
    return transcription[0]












# Convert to expected format
input_features = processor(
    waveform.squeeze().numpy(),
    sampling_rate=target_sample_rate,
    return_tensors="pt"
).input_features

input_features = input_features.to("cuda").half()

# generate token ids
predicted_ids = model.generate(input_features)
# decode token ids to text
transcription = processor.batch_decode(predicted_ids, skip_special_tokens=False)
print(transcription)
