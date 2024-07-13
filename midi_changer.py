import os
from io import BytesIO
from pydub import AudioSegment
import mido
from mido import MidiFile

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
    note_segment = note[:duration_ms]  # Обрезаем ноту до нужной продолжительности
    if len(note_segment) < duration_ms:
        note_segment = note_segment + AudioSegment.silent(duration=duration_ms - len(note_segment))  # Добавляем тишину, если необходимо
    note_segment = note_segment - (1.0 - velocity / 127.0) * 48  # Регулируем громкость по velocity
    silence_before = AudioSegment.silent(duration=start_time)  # Добавляем тишину до начала ноты
    return silence_before + note_segment

# Создание аудиотрека из MIDI файла
def create_audio_from_midi(midi_file_path, notes, output_wav_path):
    mid = MidiFile(midi_file_path)
    ticks_per_beat = mid.ticks_per_beat
    tempo = 500000  # Default tempo (microseconds per beat)
    output = AudioSegment.empty()
    note_start_times = {}

    for track in mid.tracks:
        track_time = 0
        count = 0
        for msg in track:
            if count == 1000:
                break
            track_time += msg.time
            current_time_ms = mido.tick2second(track_time, ticks_per_beat, tempo) * 1000  # Convert to milliseconds

            if msg.type == 'note_on' and msg.velocity > 0:
                note_name = get_note_name(msg.note)
                if note_name in notes:
                    note_start_times[(msg.note, msg.channel)] = current_time_ms
            elif (msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0)):
                if (msg.note, msg.channel) in note_start_times:
                    start_time = note_start_times.pop((msg.note, msg.channel))
                    print(start_time)
                    duration_ms = current_time_ms - start_time
                    note_name = get_note_name(msg.note)
                    if note_name in notes:
                        note_segment = create_note_segment(notes[note_name], start_time, duration_ms, msg.velocity)
                        output = output.overlay(note_segment, position=start_time)
            count += 1

    output.export(output_wav_path, format='wav')
    print(f'Аудио файл сохранен как {output_wav_path}')

# Пример использования
wav_folder = 'output'  # Замените на путь к вашей папке с WAV файлами
midi_file_path = 'Tokio.mid'     # Замените на путь к вашему MIDI файлу
output_wav_path = 'final.wav'     # Замените на желаемое имя выходного WAV файла

notes = load_notes(wav_folder)
file = BytesIO()
create_audio_from_midi(midi_file_path, notes, file)
file.seek(0)
with open(output_wav_path, 'wb') as f:
    f.write(file.read())
file.seek(0)
print(len(file.read()))
