from pydub import AudioSegment
from io import BytesIO
# from mutagen.oggvorbis import OggVorbis
# from mutagen.ogg import OggPage
# from mutagen.oggopus import OggOpus


# Функция для изменения частоты дискретизации
def change_sample_rate(audio: AudioSegment, sample_rate: int) -> BytesIO:
    output = BytesIO()
    audio.export(output, format="opus", parameters=["-c:a", "libopus", "-af", f'asetrate={sample_rate},aresample=48000'])
    output.seek(0)
    return output

# Функция для объединения файлов
def merge_ogg_files(files: list[BytesIO]):
    combined = AudioSegment.empty()
    for file in files:
        audio = AudioSegment.from_file(file, format="ogg")
        combined += audio
    output = BytesIO()
    combined.export(output, format="opus")
    output.seek(0)
    return output

# Главная функция
def process_and_merge_ogg(input_file):
    # Загрузить исходный файл
    original_audio = AudioSegment.from_file(input_file, format="ogg")

    # Частоты дискретизации, которые необходимо использовать
    sample_rates = [43200, 38400, 33600, 28800, 24000, 19200]

    # Создание аудио файлов с разными частотами дискретизации
    altered_audios = [change_sample_rate(original_audio, rate) for rate in sample_rates]

    # Объединение всех измененных файлов в один
    merged_audio = merge_ogg_files(altered_audios)

    return merged_audio

# Пример использования
input_ogg = BytesIO(open("black_10.ogg", "rb").read())
merged_output = process_and_merge_ogg(input_ogg)

# Сохранение объединенного файла
with open("merged_output.ogg", "wb") as f:
    f.write(merged_output.read())
