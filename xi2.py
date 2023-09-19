"""Parse xi2 code and convert to MIDI."""

import argparse
import re

import midi
from renderer import render


def parse(t):
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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tempo', help='tempo in bpm', default=120, type=int)
    parser.add_argument('-o', '--offset', help='key offset', default=60, type=int)
    parser.add_argument('infile')
    parser.add_argument('outfile')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    with open(args.infile) as fh:
        lines = fh.readlines()

    ll = ''.join(lines)
    # remove whitespace
    ll = re.sub('[ \t]', '', ll)
    # remove comments
    ll = re.sub('#[^\n]*', '', ll)

    # expand macros
    ll = ll.replace('\n', r'\n')
    while re.search(r'(\[[^\]]*\]):(.*)', ll):
        match = re.search(r'(\[[^\]]*\]):(.*)', ll)
        key, after = match.groups()
        if after.startswith(r'\n'):
            val = after.split('[end]', 1)[0]
            ll = ll.replace('%s:%s[end]' % (key, val), '')
        else:
            val = after.split(r'\n', 1)[0]
            ll = ll.replace('%s:%s' % (key, val), '')
        ll = ll.replace(key, val)
    ll = ll.replace(r'\n', '\n')

    # trim newlines
    ll = ll.strip('\n')
    ll = re.sub('\n\n+', '\n\n', ll)

    # join tracks from different sections
    tracks = dict()
    for section in ll.split('\n\n'):
        length = max([len(t) for t in tracks.values()], default=0)
        for track in section.split('\n'):
            try:
                name, data = track.split(':', 1)
            except Exception:
                print(track)
                raise
            if name not in tracks:
                tracks[name] = []
            tracks[name] += [''] * (length - len(tracks[name]))
            tracks[name] += parse(data)

    # create first track with meta infos
    midi_tracks = []
    t0 = midi.Midi()
    t0.set_tempo(args.tempo)
    midi_tracks.append(t0)

    ch = 0
    for name, track in tracks.items():
        m = midi.Midi()
        # write meta info
        m.meta_event_str(0, 0x04, name)
        try:
            prog = int(name)
        except ValueError:
            prog = 0
        m.prog_ch(0, ch, prog)
        # write data
        render(track, m, ch=ch, offset=args.offset)
        # write
        midi_tracks.append(m)
        ch += 1

    with open(args.outfile, 'wb') as fh:
        midi.write_file(fh, midi_tracks)
