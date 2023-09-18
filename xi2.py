import argparse
import re
from iparser import IParser
from midi import Midi, MidiFile

"""Parse xi2 code and convert to MIDI."""

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--tempo', help="tempo in bpm", default=120, type=int)
parser.add_argument('-o', '--offset', help="key offset", default=60, type=int)
parser.add_argument('infile')
parser.add_argument('outfile')
args = parser.parse_args()

def length(data):
    data = re.sub('{[^}]*}', '', data)
    data = re.sub('\([^\)]*\)', '', data)
    return len(data.split(',')) - 1

f = open(args.infile)
lines = f.readlines()
f.close()

ll = ''.join(lines)
# remove whitespace
ll = re.sub('[ \t]', '', ll)
# remove c++ style comments
# we have to escape linebreaks
ll = re.sub('\n', '\\\\n', ll)
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

# remove trailing newlines
ll = re.sub('^\n*', '', ll)
# remove \n\n+
ll = re.sub('\n', '\\\\n', ll)
ll = re.sub('\\\\n(\\\\n)+', '\\\\n\\\\n', ll)
ll = re.sub('\\\\n', '\n', ll)
# remove newlines at the end
ll = re.sub('\n*$', '', ll)

def parse(t):
    string = ''
    stack = [[]]
    for c in t:
        #print stack, string, c
        if c == '{':
            stack.append([])
        elif c == '}':
            stack[-1].append(string)
            string = tuple(stack.pop())
        elif c == '(':
            stack.append([])
        elif c == ')':
            stack[-1].append(string)
            string = stack.pop()
        elif c == ',':
            stack[-1].append(string)
            string = ''
        else:
            string += c
    return stack[0]

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
        except Exception, e:
            print track
            raise e
        data = parse(data)
        if not tracks.has_key(name):
            tracks[name] = [''] * l
        tracks[name] += data
    if len(tracks) == 0:
        l = 0
    else:
        l = max([len(t) for t in tracks])
    for (name,data) in tracks.iteritems():
        data += [''] * (l - len(data))

# create midi
mf = MidiFile()

# create first track with meta infos
m = Midi()
m.set_tempo(args.tempo)
mf.add_track(m)

ch = 0
for name, track in tracks.iteritems():
    m = Midi()
    # write meta info
    m.meta_event(0, 0x04, len(name), name)
    try:
        prog = int(name)
    except ValueError:
        prog = 0
    m.prog_ch(0, ch, prog)
    # write data
    ip = IParser(track, ch=ch, offset=args.offset)
    m += ip.midi
    # write
    mf.add_track(m)
    ch += 1

# write to file
mf.write(args.outfile)
