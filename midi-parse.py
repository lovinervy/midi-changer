import argparse
from mido import MidiFile

def midi_parser(input_midi_path: str, output_txt_path: str):
    midi = MidiFile(input_midi_path)
    for num, track in enumerate(midi.tracks):
        msgs = []
        for msg in track:
            msgs.append(str(msg))
            msgs.append('\n')
        path = output_txt_path.split('.txt') + [str(num), '.txt']
        local_output_path = ''.join((x for x in path if x != ''))
        with open(local_output_path, 'w') as f:
            f.writelines(msgs)


if __name__ == '__main__':
    input_midi = 'Tokio.mid'
    output_txt = 'txt_output/file.txt'
    midi_parser(input_midi, output_txt)
