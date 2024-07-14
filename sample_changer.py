from typing import Literal
from io import BytesIO

import numpy
from numpy.typing import NDArray

import scipy
from scipy.io import wavfile
from scipy.fft import fft
from scipy.signal import resample
from pydub import AudioSegment



import numpy
from io import BytesIO
from pydub import AudioSegment
from numpy.typing import NDArray
from scipy.fft import fft
from scipy.signal import resample

class AudioTransform:
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def __init__(self, audio: BytesIO) -> None:
        self.audio = audio
        self.audio_segment: AudioSegment = AudioSegment.from_file(self.audio, format='wav')

    def _detect_note_frequency(self, data: NDArray, rate: float | int) -> float:
        # Применяем FFT для преобразования сигнала из временной области в частотную
        N = len(data)
        yf = fft(data)
        xf = numpy.fft.fftfreq(N, 1 / rate)

        # Вычисляем амплитуды
        abs_yf = numpy.abs(yf)

        # Исключаем нулевые частоты
        nonzero_indices = numpy.where(xf > 0)
        xf = xf[nonzero_indices]
        abs_yf = abs_yf[nonzero_indices]

        # Создаем гистограмму амплитуд частотных составляющих
        freq_bins = numpy.linspace(0, rate / 2, num=500)
        hist, bin_edges = numpy.histogram(xf, bins=freq_bins, weights=abs_yf)

        # Находим частоту с максимальной амплитудой в гистограмме
        max_freq_idx = numpy.argmax(hist)
        freq = (bin_edges[max_freq_idx] + bin_edges[max_freq_idx + 1]) / 2

        return freq

    def _frequency_to_note(self, freq: float) -> str:
        A4 = 440.0
        C0 = A4 * pow(2, -4.75)

        h = round(12 * numpy.log2(freq / C0))
        octave = h // 12
        n = h % 12
        return f"{self.notes[n]}{octave}"

    def _note_to_frequency(self, note: str) -> float:
        A4 = 440.0
        C0 = A4 * pow(2, -4.75)

        note_name = note[:-1]
        octave = int(note[-1])
        n = self.notes.index(note_name)
        h = n + 12 * (octave - 4)
        freq = C0 * (2 ** (h / 12.0))

        return freq

    def _transpose_audio(self, semitones: float) -> AudioSegment:
        new_frame_rate = int(self.audio_segment.frame_rate * (2 ** (semitones / 12.0)))
        transposed_audio = self.audio_segment._spawn(self.audio_segment.raw_data, overrides={
            "frame_rate": new_frame_rate
        }).set_frame_rate(self.audio_segment.frame_rate)
        return transposed_audio

    def _generate_all_notes(self, base_note: str) -> dict[str, BytesIO]:
        note_files: dict[str, BytesIO] = {}
        base_freq = self._note_to_frequency(base_note)
        for octave in range(0, 9):  # Октавы от 0 до 8
            for note in self.notes:
                target_note = f"{note}{octave}"
                target_freq = self._note_to_frequency(target_note)
                semitones = 12 * numpy.log2(target_freq / base_freq)

                # Транспонируем аудиосегмент
                transposed_audio = self._transpose_audio(semitones)

                note_file = BytesIO()
                transposed_audio.export(note_file, format='wav')
                note_file.seek(0)  # Сбрасываем указатель на начало файла
                note_files[target_note] = note_file

        return note_files

    def process_audio(self):
        data = numpy.array(self.audio_segment.get_array_of_samples())
        rate = self.audio_segment.frame_rate

        freq = self._detect_note_frequency(data, rate)

        note = self._frequency_to_note(freq)
        return self._generate_all_notes(note)

if __name__ == "__main__":
    with open('sound.wav', 'rb') as f:
        file = BytesIO(f.read())
    a = AudioTransform(file)
    result = a.process_audio()
    for note, audio in result.items():
        with open(f"output/{note}.wav", "wb") as f:
            f.write(audio.read())
