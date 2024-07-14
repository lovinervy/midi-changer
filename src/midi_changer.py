from mido import MidiFile, tick2second
from pydub import AudioSegment

from .sample_changer import AudioTransform
from .utils import get_midi_duration, get_tempo


class MidiChanger:
    def __init__(self, midi: MidiFile, audio_transform: AudioTransform) -> None:
        self.midi = midi
        self._transform = audio_transform
        self.length = get_midi_duration(midi)
        self.tempo = get_tempo(midi)
        self.channel_play: dict[int, set[tuple[str, str, int]]] = {}


    def create_note_segment(self, instrumental: str, note: str, duration_ms, sustain_ms):
        note_audio = self._transform.get_sample(note)

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

        # silence_before = AudioSegment.silent(duration=start_time)  # Добавляем тишину до начала ноты
        return note_segment

    def create_timing(self, track: list):
        time = 0
        for msg in track:
            try:
                if msg.channel not in self.channel_play:
                    self.channel_play[msg.channel] = set()
            except AttributeError:
                continue
            time += msg.time
            current_time_ms = tick2second(time, self.midi.ticks_per_beat, self.tempo) * 1000  # Конвертирует в миллисекунды

            if msg.type == 'note_on' and msg.velocity > 0:
                note_name = self.__get_note_name(msg.note)
                self.channel_play[msg.channel].add(('on', note_name, current_time_ms))
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                note_name = self.__get_note_name(msg.note)
                self.channel_play[msg.channel].add(('off', note_name, current_time_ms))

    def create_track(self, channel: int):
        audio = AudioSegment.silent(duration=int(self.length * 1000))
        channel_play = sorted(self.channel_play[channel], key=lambda x: (x[2],'on' if x[0] == 'on' else 'off'))
        while len(channel_play) > 1:
            data = channel_play.pop(0)
            if len(channel_play) == 0 or data[0] == 'off':
                print("WTF", channel, data)
                continue
            for i, _data in enumerate(channel_play):
                if _data[0] == 'off' and _data[1] == data[1]:
                    end_data = channel_play.pop(i)
                    duration_ms = end_data[2] - data[2]
                    print('piano', data[1], data[2], duration_ms, int(duration_ms / 2))
                    if duration_ms == .0:
                        break
                    segment = self.create_note_segment('piano', data[1], duration_ms, int(duration_ms / 2))
                    audio = audio.overlay(segment, position=data[2])
                    break
        return audio

    def create(self):
        for track in self.midi.tracks:
            self.create_timing(track)
        audios = []
        for channel in self.channel_play.keys():
            audios.append(self.create_track(channel))
        combined_audio = AudioSegment.silent(duration=int(self.length * 1000))
        for audio in audios:
            combined_audio = combined_audio.overlay(audio)
        return combined_audio

    def __get_note_name(self, midi_note: int):
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = midi_note // 12 - 1
        note = note_names[midi_note % 12]
        return f"{note}{octave}"
