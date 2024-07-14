import os
import argparse
from io import BytesIO

from mido import MidiFile, tick2second, bpm2tempo
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
def create_note_segment(note, start_time, duration_ms, velocity, sustain_ms):
    note_audio = AudioSegment.from_file(note, format='wav')

    # Обрезаем ноту до нужной продолжительности, если она длиннее необходимого
    if len(note_audio) > duration_ms:
        note_segment = note_audio[:duration_ms]
    else:
        note_segment = note_audio

    # Если длины ноты не хватает, дублируем ноту до нужной длины
    while len(note_segment) < duration_ms + sustain_ms:
        note_segment += note_audio

    # Выделяем часть для сустейна
    if len(note_segment) > duration_ms:
        sustain_segment = note_segment[duration_ms:duration_ms + sustain_ms].fade_out(sustain_ms)
        note_segment = note_segment[:duration_ms] + sustain_segment
    else:
        sustain_segment = note_segment[:sustain_ms].fade_out(sustain_ms)
        note_segment += sustain_segment

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


def get_midi_duration(midi_file: MidiFile):
    total_time = 0
    for track in midi_file.tracks:
        time = 0
        for msg in track:
            time += msg.time
        total_time = max(total_time, time)
    return tick2second(total_time, midi_file.ticks_per_beat, bpm2tempo(120))


# Создание аудиотрека из MIDI файла
def create_audio_from_midi(midi_file_path, notes, output_wav_path):
    mid = MidiFile(midi_file_path)
    ticks_per_beat = mid.ticks_per_beat
    tempo = get_tempo(mid)
    audio_length = get_midi_duration(mid)
    print(f"Ticks per beat: {ticks_per_beat}")
    print(f"Tempo: {tempo}")
    print(f"Audio length: {audio_length:.2f} seconds ≈ {int(audio_length // 60)}:{int(audio_length % 60)} minutes")

    output_by_channel = {}
    for i in range(16):  # MIDI supports 16 channels
        output_by_channel[i] = AudioSegment.silent(int(audio_length * 1000))

    note_start_times = {}
    track_times = {i: 0 for i in range(16)}  # Отслеживаем время для каждого канала

    print("Start")
    percent_delta = 0.1
    current_percent = 0
    total_ticks = get_total_ticks(mid)

    for track in mid.tracks:
        for msg in track:
            try:
                if msg.channel not in track_times:
                    continue
            except AttributeError:
                continue
            track_times[msg.channel] += msg.time
            current_time_ms = tick2second(track_times[msg.channel], ticks_per_beat, tempo) * 1000  # Convert to milliseconds

            if msg.type == 'note_on' and msg.velocity > 0:
                note_name = get_note_name(msg.note)
                if note_name in notes:
                    note_start_times[(msg.note, msg.channel)] = current_time_ms
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if (msg.note, msg.channel) in note_start_times:
                    start_time = note_start_times.pop((msg.note, msg.channel))
                    duration_ms = current_time_ms - start_time
                    note_name = get_note_name(msg.note)
                    if note_name in notes:
                        note_segment = create_note_segment(notes[note_name], start_time, duration_ms, msg.velocity, int(duration_ms / 2))
                        output_by_channel[msg.channel] = output_by_channel[msg.channel].overlay(note_segment, position=start_time)
                    else:
                        print('Not found', note_name)
            if track_times[msg.channel] / total_ticks >= current_percent:
                print(f"{int(current_percent * 100)} %")
                current_percent += percent_delta

    combined_output = AudioSegment.silent(int(audio_length * 1000))
    for channel_output in output_by_channel.values():
        combined_output = combined_output.overlay(channel_output)

    combined_output.export(output_wav_path, format='wav')

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
