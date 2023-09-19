# https://web.archive.org/web/20131030010909/http://www.sonicspot.com/guide/midifiles.html

import io

TIME_DEVISION = 0x00c0  # two bytes


class Midi:
    """Create MIDI bytecode from MIDI events."""

    def __init__(self, fh=None):
        if fh:
            self.fh = fh
        else:
            self.fh = io.BytesIO()

    def write_fixed(self, value, size):
        if isinstance(value, bytes):
            self.fh.write((b' ' * size + value)[-size:])
        elif size != 0:
            assert isinstance(value, int)
            self.write_fixed(value >> 8, size - 1)
            self.fh.write(bytes([value & 0xff]))

    def write_variable(self, value, _rec=False):
        if value == 0 and _rec:
            return 0
        self.write_variable(value >> 7, True)
        if _rec:
            self.fh.write(bytes([(value & 0x7f) | 0x80]))
        else:
            self.fh.write(bytes([value & 0x7f]))

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

    def meta_event_str(self, dt, event, s):
        data = s.encode('ascii')
        self.meta_event(dt, event, len(data), data)

    def system_exclusive(self, dt, length, data):
        self.write_variable(int(dt * TIME_DEVISION))
        self.write_fixed(0xf0, 1)
        self.write_variable(length)
        self.write_fixed(data, length)

    def set_tempo(self, bpm):
        # midi uses microsec/quarter note
        msqn = 60_000_000 // bpm
        self.meta_event(0, 0x51, 3, msqn)

    def note_on(self, dt, ch, key, vol=1):
        self.ch_event(dt, 0x9, ch, key, int(vol * 0x7f))

    def note_off(self, dt, ch, key, vol=1):
        self.ch_event(dt, 0x8, ch, key, int(vol * 0x7f))

    def lyrics(self, dt, s):
        self.meta_event_str(dt, 0x05, s)

    def prog_ch(self, dt, ch, prog):
        self.ch_event(dt, 0xc, ch, prog)

    def ctrl_event(self, dt, ch, ctrl, v):
        self.ch_event(dt, 0xb, ch, ctrl, v)

    def set_vol(self, dt, ch, vol=1):
        self.ctrl_event(dt, ch, 0x07, int(vol * 0x7f))


def write_file(fh, tracks):
    f = Midi(fh)
    f.write_fixed(0x4D546864, 4)  # chunk ID "MThd"
    f.write_fixed(6, 4)  # chunk size
    f.write_fixed(1, 2)  # format type
    f.write_fixed(len(tracks), 2)
    f.write_fixed(TIME_DEVISION, 2)
    for track in tracks:
        f.write_fixed(0x4D54726B, 4)  # chunk ID "MTtr"
        buf = track.fh.getvalue()
        f.write_fixed(len(buf) + 4, 4)
        f.fh.write(buf)
        f.meta_event(0, 0x2f, 0, b'')  # end_track event


if __name__ == '__main__':
    # Example:
    t = Midi()
    t.set_vol(0, 1, 1)
    t.ctrl_event(0, 1, 0x00, 0)  # setting bank
    t.note_on(0.5, 1, 60)
    t.note_off(1, 1, 60)
    t.note_on(0, 1, 62)
    t.note_off(1, 1, 62)
    t.note_on(0, 1, 64)
    t.note_off(1, 1, 64)

    with open('test.mid', 'wb') as fh:
        write_file(fh, [t])
