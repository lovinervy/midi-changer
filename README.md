# midi-changer

### Unix
Требуется, чтобы были установлены: `cmake`, `ffmpeg`
Установка
```bash
python3 -m venv .venv
source ./.venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

Запуск
```bash
(.venv) pc$ python main.py -s sample.wav -m example.mid -o example-sample.wav
```