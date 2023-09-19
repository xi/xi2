"""Parse xi2 code and convert to MIDI."""

import argparse
import re
import sys

import midi
from renderer import render


def parse_seq(t):
    string = ''
    stack = [[]]
    for c in t:
        if c == '(':
            stack.append([])
        elif c == ')':
            stack[-1].append(string)
            string = stack.pop()
        elif c == '{':
            stack.append([])
        elif c == '}':
            stack[-1].append(string)
            string = set(stack.pop())
        elif c == ',':
            stack[-1].append(string)
            string = ''
        else:
            string += c
    return stack[0]


def expand_macros(s):
    s = s.replace('\n', r'\n')
    while re.search(r'(\[[^\]]*\]):(.*)', s):
        match = re.search(r'(\[[^\]]*\]):(.*)', s)
        key, after = match.groups()
        if after.startswith(r'\n'):
            val = after.split('[end]', 1)[0]
            s = s.replace('%s:%s[end]' % (key, val), '')
        else:
            val = after.split(r'\n', 1)[0]
            s = s.replace('%s:%s' % (key, val), '')
        s = s.replace(key, val)
    return s.replace(r'\n', '\n')


def parse(s):
    s = re.sub('[ \t]', '', s)
    s = re.sub('#[^\n]*', '', s)
    s = expand_macros(s)
    s = s.strip('\n')
    s = re.sub('\n\n+', '\n\n', s)

    tracks = {}
    for section in s.split('\n\n'):
        length = max([len(t) for t in tracks.values()], default=0)
        for track in section.split('\n'):
            try:
                name, data = track.split(':', 1)
            except ValueError:
                print(track)
                raise
            if name not in tracks:
                tracks[name] = []
            tracks[name] += [''] * (length - len(tracks[name]))
            tracks[name] += parse_seq(data)

    return tracks


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tempo', help='tempo in bpm', default=120, type=int)
    parser.add_argument('-o', '--offset', help='key offset', default=60, type=int)
    parser.add_argument('infile')
    parser.add_argument('outfile')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    if args.infile == '-':
        s = sys.stdin.read()
    else:
        with open(args.infile) as fh:
            s = fh.read()
    tracks = parse(s)

    # create first track with meta infos
    midi_tracks = []
    t0 = midi.Midi()
    t0.set_tempo(args.tempo)
    midi_tracks.append(t0)

    for ch, name in enumerate(tracks):
        m = midi.Midi()
        m.meta_event_str(0, 0x04, name)
        try:
            prog = int(name)
        except ValueError:
            prog = 0
        m.prog_ch(0, ch, prog)
        render(tracks[name], m, ch=ch, offset=args.offset)
        midi_tracks.append(m)

    if args.outfile == '-':
        midi.write_file(sys.stdout.buffer, midi_tracks)
    else:
        with open(args.outfile, 'wb') as fh:
            midi.write_file(fh, midi_tracks)
