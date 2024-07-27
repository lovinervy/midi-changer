from io import BytesIO
from argparse import ArgumentParser

from mido import MidiFile
from src import MidiChanger, AudioTransform


parser = ArgumentParser(
    prog="MidiChanger",
    description="Скрипт для изменение звука у миди файла",
    epilog="Внизу описаны входные аргументы для запуска скрипта"
)

parser.add_argument('-s', '--sample', required=True, help="Семпл который будет использоваться как основа (Внимение wav файл)")
parser.add_argument('-m', '--midi', required=True, help="Миди файл у который будет изменен звучание")
parser.add_argument('-o', '--output', required=True, help="Название выходного файла")

if __name__ == "__main__":
    args = parser.parse_args()
    with open(args.sample, 'rb') as f:
        sample = BytesIO(f.read())

    midi = MidiFile(args.midi)
    transform = AudioTransform(sample)
    changer = MidiChanger(midi, transform)

    audio = changer.create()
    file = BytesIO()
    audio_format = args.output.split('.')[-1]
    audio.export(file, format=audio_format)
    file.seek(0)
    with open(args.output, 'wb') as f:
        f.write(file.read())

