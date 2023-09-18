from midi import Midi
from midi import MidiFile

# The tricky part here is the time conversion.
# and noteOff events


class IParser:
    """Convert intermediate code to MIDI bytecode."""

    def __init__(self, seq, ch=0, offset=60):
        self.midi = Midi()
        self.ch = ch
        self.offset = offset
        self.dt = 0
        self.dt_stack = []
        self.stack = []
        self.parse_seq(seq)

    def dt_step(self):
        a = 1.0
        for i in self.dt_stack[1:]:
            a /= i
        return a

    def parse_el(self, e):
        if e.isdigit():  # note
            self.midi.note_on(self.dt, self.ch, self.offset + int(e), 1)
            self.dt = self.dt_step()
        elif e == '-':  # continue
            self.dt += self.dt_step()
        elif e == '':  # break
            self.dt += self.dt_step()
        else:  # lyrics
            self.midi.lyrics(self.dt, e.replace('_', ' '))
            self.dt = self.dt_step()

    def parse_seq(self, seq):
        self.dt_stack.append(len(seq))
        for e in seq:
            if type(e) == type(''):
                if e != '-':
                    self.stop()
                self.stack.append(e)
                self.parse_el(e)
            elif type(e) == type([]):
                if '-' not in e:
                    self.stop()
                self.stack.append(e)
                self.parse_set(e)
            elif type(e) == type(()):
                self.parse_seq(e)
            else:
                raise Exception("unknown element: " + e)
        self.dt_stack.pop()

    def parse_set(self, s):
        for e in s:
            if type(e) != type(''):
                raise Exception("only elements are allowed inside sets: " + e)
            elif e == '':
                raise Exception("Breaks are not allowed inside sets!")
            else:
                self.parse_el(e)
            self.dt = 0
        self.dt = self.dt_step()

    def stop(self):
        if len(self.stack) == 0:
            return
        e = self.stack.pop()
        if type(e) == type(''):
            if e == '-':
                self.stop()
            elif e == '':
                pass  # already stopped
            elif e.isdigit():
                self.midi.note_off(self.dt, self.ch, self.offset + int(e), 1)
                self.dt = 0
            else:
                pass
        elif type(e) == type([]):
            if '-' in e:
                self.stop()
            for ee in e:
                # we already checked the validity of the set when parsing.
                # we only need to check if this is a note, lyrics or '-'
                if ee.isdigit():
                    self.midi.note_off(self.dt, self.ch, self.offset + int(ee), 1)
                    self.dt = 0
        else:
            raise Exception("Unexpected object on stack: " + e)


if __name__ == '__main__':
    a = [(('0', '1'), '2'), '4', '5', '-', '', ['0', '4', '7'], '', '', '0', ['3', '-']]

    f = MidiFile()
    ip = IParser(a, 0, 60)
    f.add_track(ip.midi)
    f.write('test.mid')
