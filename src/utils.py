from mido import MidiFile, tick2second


def get_tempo(midi: MidiFile):
    for track in midi.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                return msg.tempo


def get_midi_duration(midi: MidiFile):
    """Возвращает длину трека в секундах"""
    total_time = 0
    for track in midi.tracks:
        time = sum((x.time for x in track))
        total_time = max(total_time, time)
    return tick2second(total_time, midi.ticks_per_beat, get_tempo(midi))
