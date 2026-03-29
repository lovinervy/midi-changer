#!/usr/bin/env -S uv run --script

import argparse
from pathlib import Path
from io import BytesIO

from mido import MidiFile
from src import MidiChanger, AudioTransform


def create_audio(midi_path: str | Path, tone_path: str | Path):
    with open(tone_path, "rb") as f:
        tone = BytesIO(f.read())

    midi = MidiFile(midi_path)
    transform = AudioTransform(tone)
    tone_to_song = MidiChanger(midi, transform)
    return tone_to_song.create()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--midi", "-m", help="Входной миди файл", required=True)
    parser.add_argument("--tone", "-t", help="Входной тон/звук (wav файл)", required=True)
    parser.add_argument("--output", "-o", help="Выходной файл", required=True)
    parser.add_argument("--format", "-f", help="Формат аудио", default="mp3")
    parser.add_argument(
        "--codec", "-c", help="Кодек формата выходного файла", default=None
    )

    try:
        args = parser.parse_args()
        audio = create_audio(args.midi, args.tone)

        output = (
            args.output
            if args.output.endswith(args.format)
            else f"{args.output}.{args.format}"
        )
        audio.export(output, args.format, args.codec)
        print("Готово", output)
    except Exception as e:
        print(str(e))


if __name__ == "__main__":
    main()
