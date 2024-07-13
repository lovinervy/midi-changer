import os
import argparse
from io import BytesIO

from mido import MidiFile, tick2second
from pydub import AudioSegment

from sample_changer import AudioTransform


# Загрузка всех нот в словарь
def load_notes(wav_folder):
    notes = {}
    for file_name in os.listdir(wav_folder):
        if file_name.endswith('.wav'):
            note_name = file_name[:-4]
            note_path = os.path.join(wav_folder, file_name)
            notes[note_name] = AudioSegment.from_file(note_path, format='wav')
    return notes

# Получение имени ноты по значению MIDI
def get_note_name(midi_note):
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = midi_note // 12 - 1
    note = note_names[midi_note % 12]
    return f"{note}{octave}"

# Создание аудиосегмента для каждой ноты
def create_note_segment(note, start_time, duration_ms, velocity):
    note_audio = AudioSegment.from_file(note, format='wav')
    note_segment = note_audio[:duration_ms]  # Обрезаем ноту до нужной продолжительности
    if len(note_segment) < duration_ms:
        note_segment = note_segment + AudioSegment.silent(duration=duration_ms - len(note_segment))  # Добавляем тишину, если необходимо
    # note_segment = note_segment - (1.0 - velocity / 127.0) * 48  # Регулируем громкость по velocity
    silence_before = AudioSegment.silent(duration=start_time)  # Добавляем тишину до начала ноты
    return silence_before + note_segment


def get_tempo(midi_file: MidiFile):
    tempo = 0
    count_tempo = 0
    for track in midi_file.tracks:
        for msg in track:
            match msg.type:
                case "set_tempo":
                    count_tempo += 1
                    tempo = msg.tempo
    print(f"Found tempo: {count_tempo}")
    return tempo


def get_total_ticks(midi_file: MidiFile):
    count = 0
    for track in midi_file.tracks:
        for msg in track:
            if msg.type in ("note_on", "note_off"):
                count += msg.time
    print(f"Has {count} ticks")
    return count


# Создание аудиотрека из MIDI файла
def create_audio_from_midi(midi_file_path, notes, output_wav_path):
    mid = MidiFile(midi_file_path)
    ticks_per_beat = mid.ticks_per_beat
    tempo = get_tempo(mid)  # Default tempo (microseconds per beat)
    ticks = get_total_ticks(mid)
    audio_length = round(ticks / ticks_per_beat * tempo / 1000)
    print(f"Audio length: {audio_length} milliseconds ≈ {audio_length / 1000 / 60: .2f} minutes")
    output = AudioSegment.silent(audio_length)
    note_start_times = {}

    print("Start")
    percent_delta = 0.1
    current_percent = 0
    for track in mid.tracks:
        track_time = 0

        for msg in track:
            track_time += msg.time
            current_time_ms = tick2second(track_time, ticks_per_beat, tempo) * 1000  # Convert to milliseconds

            if msg.type == 'note_on' and msg.velocity > 0:
                note_name = get_note_name(msg.note)
                if note_name in notes:
                    note_start_times[(msg.note, msg.channel)] = current_time_ms
            elif (msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0)):
                if (msg.note, msg.channel) in note_start_times:
                    start_time = note_start_times.pop((msg.note, msg.channel))
                    duration_ms = current_time_ms - start_time
                    note_name = get_note_name(msg.note)
                    if note_name in notes:
                        note_segment = create_note_segment(notes[note_name], start_time, duration_ms, msg.velocity)
                        output = output.overlay(note_segment, position=start_time)
            if track_time / ticks >= current_percent:
                print(f"{int(current_percent * 100)} %")
                current_percent += percent_delta


    output.export(output_wav_path, format='wav')

SAMPLE_FOLDER = 'output'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--midi', type=str)
    parser.add_argument('--sample', type=str)
    parser.add_argument('--output', type=str)
    args = parser.parse_args()

    with open(args.sample, 'rb') as f:
        sample = BytesIO(f.read())
    transform = AudioTransform(sample)
    notes = transform.process_audio()

    # notes = load_notes(SAMPLE_FOLDER)
    file = BytesIO()
    create_audio_from_midi(args.midi, notes, file)
    file.seek(0)
    with open(args.output, 'wb') as f:
        f.write(file.read())
    file.seek(0)
    print(f'Audio save as: {args.output}')
    print("Size: ",round(len(file.read()) / 1024**2, 3), "Mb")
