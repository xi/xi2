import midi


class Renderer:
    """Convert intermediate code to MIDI bytecode."""

    def __init__(self, midi, ch=0, offset=60):
        self.midi = midi
        self.ch = ch
        self.offset = offset
        self.dt = 0
        self.active_notes = set()

    def note_on(self, s):
        note = int(s, 10) + self.offset
        self.midi.note_on(self.dt, self.ch, note, 1)
        self.active_notes.add(note)
        self.dt = 0

    def lyrics(self, s):
        self.midi.lyrics(self.dt, s.replace('_', ' '))
        self.dt = 0

    def stop(self):
        while self.active_notes:
            self.midi.note_off(self.dt, self.ch, self.active_notes.pop(), 1)
            self.dt = 0

    def render_seq(self, seq, step=1.0):
        for item in seq:
            if isinstance(item, set):
                if '-' not in item:
                    self.stop()
                for subitem in item:
                    if subitem == '-':
                        continue
                    elif subitem.isdigit():
                        self.note_on(subitem)
                    else:
                        self.lyrics(subitem)
                self.dt = step
            elif isinstance(item, list):
                self.render_seq(item, step / len(item))
            elif item == '-':
                self.dt += step
            elif item == '':
                self.stop()
                self.dt += step
            elif item.isdigit():
                self.stop()
                self.note_on(item)
                self.dt = step
            else:
                self.stop()
                self.lyrics(item)
                self.dt = step


def render(seq, midi, ch=0, offset=60):
    r = Renderer(midi, ch, offset)
    r.render_seq(seq)
    r.stop()


if __name__ == '__main__':
    a = [[['0', '1'], '2'], '4', '5', '-', '', {'0', '4', '7'}, '', '', '0', {'3', '-'}]
    t = midi.Midi()
    render(a, t)

    with open('test.mid', 'wb') as fh:
        midi.write_file(fh, [t])
