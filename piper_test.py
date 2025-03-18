import piper

# Initialize the TTS model
synthesizer = piper_test.Synthesizer(model_path="path/to/piper_model")

# Generate speech from text
text = "Hello, how are you doing?"
speech = synthesizer.text_to_speech(text)

# Save the output as an audio file
with open("output.wav", "wb") as f:
    f.write(speech)
