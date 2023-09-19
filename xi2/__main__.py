"""Parse xi2 code and convert to MIDI."""

import argparse
import re
import sys

from . import midi
from .renderer import render


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
    s = re.sub('[ \t]', '', s)
    s = re.sub('#.*', '', s)
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
    s = s.replace(r'\n', '\n')
    s = s.strip('\n')
    return re.sub('\n\n+', '\n\n', s)


def parse(s):
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
    parser.add_argument('-d', '--debug', help='print normalized input and exit', action='store_true')
    parser.add_argument('infile')
    parser.add_argument('outfile')
    return parser.parse_args()


def main():
    args = parse_args()

    if args.infile == '-':
        s = sys.stdin.read()
    else:
        with open(args.infile) as fh:
            s = fh.read()

    s = expand_macros(s)
    if args.debug:
        print(s)
        sys.exit(0)

    tracks = parse(s)

    # create first track with meta infos
    midi_tracks = []
    t0 = midi.Midi()
    t0.set_tempo(args.tempo)
    midi_tracks.append(t0)

    for ch, name in enumerate(tracks):
        midi_tracks.append(
            render(name, tracks[name], ch=ch, offset=args.offset)
        )

    if args.outfile == '-':
        midi.write_file(sys.stdout.buffer, midi_tracks)
    else:
        with open(args.outfile, 'wb') as fh:
            midi.write_file(fh, midi_tracks)


if __name__ == '__main__':
    main()
