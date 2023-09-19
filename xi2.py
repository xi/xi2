"""Parse xi2 code and convert to MIDI."""

import argparse
import re

import midi
from renderer import Renderer


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
    # remove c++ style comments
    # we have to escape linebreaks
    ll = re.sub('\n', r'\\n', ll)
    ll = re.sub('/\*[^(\*)]*\*/', '', ll)
    ll = re.sub('\\\\n', '\n', ll)
    # remove c style comments
    ll = re.sub('//[^\n]*\n', '', ll)

    # expand macros
    ll = re.sub('\n', '\\\\n', ll)
    while re.search('(\[[^\]]*\]):(.*)', ll):
        match = re.search('(\[[^\]]*\]):(.*)', ll)
        (key, after) = match.groups()
        if after.startswith('<<'):
            eol = after.split('\\n',1)[0][2:]
            val = after.split(eol,2)[1]
            ll = re.sub(re.escape("%s:<<%s%s%s" % (key, eol, val, eol)), '', ll)
        else:
            val = after.split('\\n',1)[0]
            ll = re.sub(re.escape("%s:%s" % (key, val)), '', ll)
        ll = re.sub(re.escape(key), val, ll)
    ll = re.sub('\\\\n', '\n', ll)

    # trim newlines
    ll = ll.strip('\n')
    ll = re.sub('\n\n+', '\n\n', ll)

    # join track parts from different sets
    tracks = dict()
    for s in ll.split('\n\n'):
        if len(tracks) == 0:
            l = 0
        else:
            l = max([len(t) for t in tracks])
        for track in s.split('\n'):
            try:
                (name, data) = track.split(':', 1)
            except Exception:
                print(track)
                raise
            data = parse(data)
            if name not in tracks:
                tracks[name] = [''] * l
            tracks[name] += data
        if len(tracks) == 0:
            l = 0
        else:
            l = max([len(t) for t in tracks])
        for name, data in tracks.items():
            data += [''] * (l - len(data))

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
        Renderer(m, track, ch=ch, offset=args.offset)
        # write
        midi_tracks.append(m)
        ch += 1

    with open(args.outfile, 'wb') as fh:
        midi.write_file(fh, midi_tracks)
