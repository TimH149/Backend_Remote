import sounddevice as sd
from scipy.io.wavfile import write

sample_rate = 16000
duration = 5

print("Recording...")
audio = sd.rec(
    int(duration * sample_rate),
    samplerate=sample_rate,
    channels=1,
    dtype="int16",
)
sd.wait()

write("test.wav", sample_rate, audio)

print("Saved as test.wav")