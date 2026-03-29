from io import BytesIO
from abc import ABC, abstractmethod

import numpy as np
from scipy.fft import fft
from pydub import AudioSegment


class FrequencyDetector:
    def __init__(self, audio: BytesIO) -> None:
        self.audio = audio
        self.audio_segment: AudioSegment = AudioSegment.from_wav(audio)
        self.sample_rate = self.audio_segment.frame_rate
        self.base_freq = self.detect_frequency()

    def detect_frequency(self) -> float:
        data = np.array(self.audio_segment.get_array_of_samples())
        # Применяем FFT для преобразования сигнала из временной области в частотную
        N = len(data)
        yf = fft(data)
        xf = np.fft.fftfreq(N, 1 / self.sample_rate)

        # Вычисляем амплитуды
        abs_yf = np.abs(yf)

        # Исключаем нулевые частоты
        nonzero_indices = np.where(xf > 0)
        xf = xf[nonzero_indices]
        abs_yf = abs_yf[nonzero_indices]

        # Создаем гистограмму амплитуд частотных составляющих
        freq_bins = np.linspace(0, self.sample_rate / 2, num=500)
        hist, bin_edges = np.histogram(xf, bins=freq_bins, weights=abs_yf)

        # Находим частоту с максимальной амплитудой в гистограмме
        max_freq_idx = np.argmax(hist)
        freq = (bin_edges[max_freq_idx] + bin_edges[max_freq_idx + 1]) / 2

        return freq


class SampleTransformer(ABC):
    NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    OCTAVES = [x for x in range(9)]

    def __init__(self, audio: BytesIO) -> None:
        self.SEMITONES = self._generate_semitones()
        print("Semitones:", self.SEMITONES)
        self.transform = FrequencyDetector(audio)
        self._samples: dict[str, AudioSegment] = {}
        self.base_note = self._frequency_to_note(self.transform.base_freq)

    def get_sample(self, note: str, skip: bool = False) -> AudioSegment | None:
        if note not in self.SEMITONES:
            if skip:
                return None
            raise ValueError(f"Unexpected note: {note}")
        if note not in self._samples:
            freq = self._note_to_frequency(note)
            self._samples[note] = self._generate_sample(freq)
        return self._samples[note]

    @abstractmethod
    def _generate_semitones(self):
        pass

    @abstractmethod
    def _note_to_frequency(self, note: str) -> float:
        pass

    @abstractmethod
    def _frequency_to_note(self, frequency: float) -> str:
        pass

    @abstractmethod
    def _generate_sample(self, frequency: float) -> AudioSegment:
        pass



class PianoSampleTransformer(SampleTransformer):
    def _generate_semitones(self):
        semitones = []
        for note in self.NOTES:
            for octave in self.OCTAVES:
                semitones.append(f"{note}{octave}")
        return semitones

    def _frequency_to_note(self, frequency: float) -> str:
        A4 = 440.0  # Частота ноты A4
        A0 = A4 * pow(
            2, -4.75
        )  # Частота ноты C0, от которой отсчитываются все остальные ноты

        h = round(12 * np.log2(frequency / A0))  # Вычисляем количество полутонов от C0
        octave = h // 12
        note_index = h % 12
        note_name = self.NOTES[note_index]
        return f"{note_name}{octave}"

    def _note_to_frequency(self, note: str) -> float:
        """Преобразует ноту в частоту на основе базовой частоты и количества полутонов."""
        A4 = 440.0  # Частота ноты A4
        A0 = A4 * pow(
            2, -4.75
        )

        note_name = note[:-1]  # Извлекаем имя ноты (без октавы)
        octave = int(note[-1])  # Извлекаем октаву из ноты
        n = self.NOTES.index(note_name)
        h = n + 12 * (octave - 4)  # Вычисляем количество полутонов от A4
        freq = A0 * (
            2 ** (h / 12.0)
        )  # Вычисляем частоту ноты на основе количества полутонов от A0

        return freq

    def _generate_sample(self, frequency: float) -> AudioSegment:
        semitones = 12 * np.log2(frequency / self._note_to_frequency(self.base_note))

        frame_rate = self.transform.audio_segment.frame_rate
        new_frame_rate = int(frame_rate * (2 ** (semitones / 12)))
        return self.transform.audio_segment._spawn(
            self.transform.audio_segment.raw_data, overrides={"frame_rate": new_frame_rate}
        ).set_frame_rate(frame_rate)


class HumanSampleTransformer(SampleTransformer):
    def _generate_semitones(self):
        semitones = []
    
        min_note = "C3"
        max_note = "F6"

        for note_index, note in enumerate(self.NOTES):
            for octave_index, octave in enumerate(self.OCTAVES):
                note_name = f"{note}{octave}"
                if self._note_to_frequency(note_name) < self._note_to_frequency(min_note):
                    continue
                if self._note_to_frequency(note_name) > self._note_to_frequency(max_note):
                    continue
                semitones.append(f"{note}{octave}")
        return semitones

    def _frequency_to_note(self, frequency: float) -> str:
        A4 = 440.0  # Частота ноты A4
        A0 = A4 * pow(
            2, -4.75
        )  # Частота ноты C0, от которой отсчитываются все остальные ноты

        h = round(12 * np.log2(frequency / A0))  # Вычисляем количество полутонов от C0
        octave = h // 12
        note_index = h % 12
        note_name = self.NOTES[note_index]
        return f"{note_name}{octave}"

    def _note_to_frequency(self, note: str) -> float:
        """Преобразует ноту в частоту на основе базовой частоты и количества полутонов."""
        A4 = 440.0  # Частота ноты A4
        A0 = A4 * pow(
            2, -4.75
        )

        note_name = note[:-1]  # Извлекаем имя ноты (без октавы)
        octave = int(note[-1])  # Извлекаем октаву из ноты
        n = self.NOTES.index(note_name)
        h = n + 12 * (octave - 4)  # Вычисляем количество полутонов от A4
        freq = A0 * (
            2 ** (h / 12.0)
        )  # Вычисляем частоту ноты на основе количества полутонов от A0

        return freq

    def _generate_sample(self, frequency: float) -> AudioSegment:
        OUTPUT_MIN = 27.5
        OUTPUT_MAX = 4186.0

        base_freq = self._note_to_frequency(self.base_note)
        base_freq = np.clip(base_freq, OUTPUT_MIN, OUTPUT_MAX) # Ограничиваем базовую частоту в пределах допустимых значений
        frame_rate = self.transform.audio_segment.frame_rate

        # пересчёт в семитоны относительно base_freq WAV
        semitones = 12 * np.log2(frequency / base_freq)
        new_frame_rate = int(frame_rate * (2 ** (semitones / 12)))
    
        return self.transform.audio_segment._spawn(
            self.transform.audio_segment.raw_data, overrides={"frame_rate": new_frame_rate}
        ).set_frame_rate(frame_rate)