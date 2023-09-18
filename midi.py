# http://www.sonicspot.com/guide/midifiles.html

TIME_DEVISION = 0x00c0 # two bytes


class Midi:
    """Create MIDI bytecode from MIDI events."""

    def __init__(self):
        self._buf = ''

    def __str__(self):
        return self._buf.encode('hex')

    def __add__(self, other):
        m = Midi()
        m._buf = self._buf + other._buf
        return m

    def write(self, name):
        f = open(name, 'w')
        f.write(self._buf)
        f.close()

    def write_fixed(self, n, k):
        if type(n) == type(''):
            self._buf += (' '*k + n)[-k:]
        else:
            if k != 0:
                self.write_fixed(n / 0x100, k-1)
                self._buf += chr(n % 0x100)

    def write_variable(self, n, _rec=False):
        # b = bin(a)[2:]; eval('0b'+''.join([b[k*8:(k+1)*8][1:] for k in range(int(len(b)/8))]))
        if n == 0 and _rec:
            return 0
        self.write_variable(n / 0x80, True)
        if _rec:
            self._buf += chr(n % 0x80 + 0x80)
        else:
            self._buf += chr(n % 0x80)

    def ch_event(self, dt, event, ch, p1, p2=-1):
        self.write_variable(int(dt * TIME_DEVISION))
        self.write_fixed((event << 4) + ch, 1)
        self.write_fixed(p1, 1)
        if not p2 == -1:
            self.write_fixed(p2, 1)

    def meta_event(self, dt, event, length, data):
        self.write_variable(int(dt * TIME_DEVISION))
        self.write_fixed(0xff, 1)
        self.write_fixed(event, 1)
        self.write_variable(length)
        self.write_fixed(data, length)

    def sys_ex(self, dt, length, data):
        self.write_variable(int(dt * TIME_DEVISION))
        self.write_fixed(0xf0, 1)
        self.write_variable(length)
        self.write_fixed(data, length)

    def set_tempo(self, bpm):
        # midi uses microsec/quarter note
        msqn = 60000000/bpm
        self.meta_event(0, 0x51, 3, msqn)

    def note_on(self, dt, ch, key, vol=1):
        self.ch_event(dt, 0x9, ch, key, int(vol * 0x7f))

    def note_off(self, dt, ch, key, vol=1):
        self.ch_event(dt, 0x8, ch, key, int(vol * 0x7f))

    def lyrics(self, dt, s):
        self.meta_event(dt, 0x05, len(s), s)

    def prog_ch(self, dt, ch, prog):
        self.ch_event(dt, 0xc, ch, prog)

    def ctrl_event(self, dt, ctrl, v):
        self.ch_event(dt, 0xb, ch, ctrl, v)

    def set_vol(self, dt, ch, vol=1):
        self.ctrl_event(dt, ch, 0x07, int(vol * 0x7f))


class MidiFile(Midi):
    def __init__(self):
        Midi.__init__(self)
        self._tracks = []

    def update(self):
        self._buf = ''
        self.write_fixed(0x4D546864, 4)  # chunk ID "MThd"
        self.write_fixed(6, 4)  # chunk size
        self.write_fixed(1, 2)  # format type
        self.write_fixed(len(self._tracks), 2)  # numer of tracks
        self.write_fixed(TIME_DEVISION, 2)  # time devision
        for track in self._tracks:
            self.write_fixed(0x4D54726B, 4)  # chunk ID "MTtr"
            self.write_fixed(len(track._buf)+4, 4)  # chunk size
            self._buf += track._buf
            self.meta_event(0, 0x2f, 0, '')  # end_track event

    def add_track(self, data, update=True):
        self._tracks.append(data)
        if update:
            self.update()


if __name__ == '__main__':
    # Example:
    f = MidiFile()
    f.add_track(Midi())
    t = Midi()
    t.set_vol(0, 1, 1)
    t.ctrl_event(0, 1, 0x00, 0)  # setting bank
    t.note_on(0.5, 1, 60)
    t.note_off(1, 1, 60)
    t.note_on(0, 1, 62)
    t.note_off(1, 1, 62)
    t.note_on(0, 1, 64)
    t.note_off(1, 1, 64)
    f.add_track(t)
    print f
    f.write('test.mid')
