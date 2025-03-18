from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torchaudio # type: ignore
from transformers import BitsAndBytesConfig
import torch # type: ignore

quant_config= BitsAndBytesConfig(
    load_in_8bit=True,  # Use 8-bit quantization
    bnb_8bit_compute_dtype=torch.bfloat16,
    bnb_8bit_use_double_quant=True
)

# load model and processor

whisper_path = "C:\\Users\\PC_LUNA\\Documents\\wikibot\\whisper-small"
processor = WhisperProcessor.from_pretrained(whisper_path)

model = WhisperForConditionalGeneration.from_pretrained(
    whisper_path,  
    quantization_config=quant_config, 
    device_map = "cuda")

model.config.forced_decoder_ids = None


# Load local audio file
audio_path = "audio/test.mp3"


def transcribe(audio):
    # Load audio and preprocess
    print("loading audio")
    waveform, sample_rate = torchaudio.load(audio)

    print("resampling audio")
    resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
    waveform = resampler(waveform)
    
    # Move input features to GPU and convert to float16 for efficiency
    print("processing audio")
    input_features = processor(waveform.squeeze().numpy(), sampling_rate=16000, return_tensors="pt").input_features
    input_features = input_features.to("cuda").half()

    # Generate transcription
    print("generating transcription")
    predicted_ids = model.generate(input_features)
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
    
    print("optimizing resources and exporting transcription")
    del waveform, resampler, input_features,predicted_ids
    torch.cuda.empty_cache()
    return transcription[0]


