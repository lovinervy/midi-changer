from mido import MidiFile

def get_duration_per_tick(tempo: int):
    second_per_tick = tempo / 10**6 / 8
    return second_per_tick


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

def get_length(midi_path: str):
    midi_file = MidiFile(midi_path)
    print(midi_file.ticks_per_beat)
    tempo = get_tempo(midi_file)
    duration_per_tick = get_duration_per_tick(tempo)
    ticks = get_total_ticks(midi_file) / 24

    print(f"Midi Length: {duration_per_tick * ticks} seconds, or {duration_per_tick * ticks / 60} mintues")


if __name__ == "__main__":
    file = "Tokio.mid"
    get_length(file)
