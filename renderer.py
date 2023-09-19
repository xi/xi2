import midi

# The tricky part here is the time conversion.
# and noteOff events


class Renderer:
    """Convert intermediate code to MIDI bytecode."""

    def __init__(self, midi, seq, ch=0, offset=60):
        self.midi = midi
        self.ch = ch
        self.offset = offset
        self.dt = 0
        self.dt_stack = []
        self.stack = []
        self.render_seq(seq)

    def dt_step(self):
        a = 1.0
        for i in self.dt_stack[1:]:
            a /= i
        return a

    def render_element(self, e):
        if e.isdigit():  # note
            self.midi.note_on(self.dt, self.ch, self.offset + int(e), 1)
            self.dt = self.dt_step()
        elif e == '-':  # hold
            self.dt += self.dt_step()
        elif e == '':  # break
            self.dt += self.dt_step()
        else:  # lyrics
            self.midi.lyrics(self.dt, e.replace('_', ' '))
            self.dt = self.dt_step()

    def render_seq(self, seq):
        self.dt_stack.append(len(seq))
        for e in seq:
            if isinstance(e, str):
                if e != '-':
                    self.stop()
                self.stack.append(e)
                self.render_element(e)
            elif isinstance(e, set):
                if '-' not in e:
                    self.stop()
                self.stack.append(e)
                self.render_chord(e)
            elif isinstance(e, list):
                self.render_seq(e)
            else:
                raise ValueError("unknown element: " + e)
        self.dt_stack.pop()

    def render_chord(self, s):
        for e in s:
            if not isinstance(e, str):
                raise ValueError("only elements are allowed inside chords: " + e)
            elif e == '':
                raise ValueError("Breaks are not allowed inside sets!")
            else:
                self.render_element(e)
            self.dt = 0
        self.dt = self.dt_step()

    def stop(self):
        if len(self.stack) == 0:
            return
        e = self.stack.pop()
        if isinstance(e, str):
            if e == '-':
                self.stop()
            elif e == '':
                pass  # already stopped
            elif e.isdigit():
                self.midi.note_off(self.dt, self.ch, self.offset + int(e), 1)
                self.dt = 0
            else:
                pass
        elif isinstance(e, set):
            if '-' in e:
                self.stop()
            for ee in e:
                # we already checked the validity of the set when parsing.
                # we only need to check if this is a note, lyrics or '-'
                if ee.isdigit():
                    self.midi.note_off(self.dt, self.ch, self.offset + int(ee), 1)
                    self.dt = 0
        else:
            assert False, "Unexpected object on stack: " + e


if __name__ == '__main__':
    a = [[['0', '1'], '2'], '4', '5', '-', '', {'0', '4', '7'}, '', '', '0', {'3', '-'}]
    t = midi.Midi()
    ip = Renderer(t, a, 0, 60)

    with open('test.mid', 'wb') as fh:
        midi.write_file(fh, [t])
