# midi-changer

Небольшой CLI скрипт, который берет миди и некий звук и на основе звука формирует новые новые нотные звучания и проигрывает как указаны ноты в midi.

### Требования к установке

- [git](https://git-scm.com)
- [uv](https://docs.astral.sh/uv/)
- [ffmpeg](https://ffmpeg.org)

> ffmpeg нужно добавить в `$PATH` для того, чтобы работала библиотека `pydub`


### Первоначальная настройка

```bash
git clone https://github.com/lovinervy/midi-changer.git
cd midi-changer
chmod +x midi-changer.py
```

### Пример запуска

```bash
./midi-changer.py -t=./black_10-c.wav -m=./input/cinder.mid -o=cinder-test-1.mp3
```
