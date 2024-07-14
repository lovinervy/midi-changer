from io import BytesIO

from mido import MidiFile
from src import MidiChanger, AudioTransform


with open('audio.wav', 'rb') as f:
    sample = BytesIO(f.read())

midi = MidiFile('SMASH MOUTH.All star.mid')
transform = AudioTransform(sample)
changer = MidiChanger(midi, transform)

audio = changer.create()
file = BytesIO()
audio.export(file, format='wav')
file.seek(0)
with open('test1234.wav', 'wb') as f:
    f.write(file.read())

