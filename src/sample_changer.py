from io import BytesIO
from typing import Literal

import numpy
from scipy.fft import fft
from pydub import AudioSegment
from numpy.typing import NDArray


class AudioTransform:
    NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    OCTAVES = [x for x in range(9)]

    def __init__(self, audio: BytesIO) -> None:
        self.SEMITONES = self.__generate_semitones()
        self.audio = audio
        self.audio_segment: AudioSegment = AudioSegment.from_wav(audio)

        # Определяем частоту ноты в семпл
        data = numpy.array(self.audio_segment.get_array_of_samples())
        rate = self.audio_segment.frame_rate
        freq = self._detect_note_frequency(data, rate)
        # Определяем ноту по частоте
        self.base_note = self._frequency_to_note(freq)
        self.base_freq = self._note_to_frequency(self.base_note)


        self.__SAMPLES: dict[str, dict[str, AudioSegment]] = {}

    def get_sample(self, note: str, sample_type: Literal['piano']='piano'):
        if not note in self.SEMITONES:
            raise ValueError(f"Unexpected note: {note}")
        if not sample_type in self.__SAMPLES:
            self.__SAMPLES[sample_type] = {}
        if not note in self.__SAMPLES[sample_type]:
            self.__SAMPLES[sample_type][note] = self.__generate_sample(note, sample_type)
        return self.__SAMPLES[sample_type][note]


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

    def _note_to_frequency(self, note: str) -> float:
        A4 = 440.0
        C0 = A4 * pow(2, -4.75)

        note_name = note[:-1]
        octave = int(note[-1])
        n = self.NOTES.index(note_name)
        h = n + 12 * (octave - 4)
        freq = C0 * (2 ** (h / 12.0))

        return freq

    def _frequency_to_note(self, freq: float) -> str:
        A4 = 440.0
        C0 = A4 * pow(2, -4.75)

        h = round(12 * numpy.log2(freq / C0))
        octave = h // 12
        n = h % 12
        return f"{self.NOTES[n]}{octave}"

    def _transpose_audio(self, semitones: float) -> AudioSegment:
        new_frame_rate = int(self.audio_segment.frame_rate * (2 ** (semitones / 12.0)))
        transposed_audio = self.audio_segment._spawn(self.audio_segment.raw_data, overrides={
            "frame_rate": new_frame_rate
        }).set_frame_rate(self.audio_segment.frame_rate)
        return transposed_audio

    def __generate_semitones(self) -> list[str]:
        semitones = []
        for note in self.NOTES:
            for octave in self.OCTAVES:
                semitones.append(f"{note}{octave}")
        return semitones

    def __generate_sample(self, note: str, sample_type: Literal['piano']):
        target_freq = self._note_to_frequency(note)
        match sample_type:
            case 'piano':
                semitones = 12 * numpy.log2(target_freq / self.base_freq)
            case _:
                raise ValueError('Unexpected sample_type')
        return self._transpose_audio(semitones)
