#!/usr/bin/env python

# http://www.sonicspot.com/guide/midifiles.html

timeDevision = 0x00c0 # two bytes

class Midi:
# creates midi bytecode from midi events

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

    def writeFixed(self, n, k):
        if type(n) == type(''):
            self._buf += (' '*k + n)[-k:]
        else:
            if k != 0:
                self.writeFixed(n / 0x100, k-1)
                self._buf += chr(n % 0x100)

    def writeVariable(self, n, _rec=False):
        # b = bin(a)[2:]; eval('0b'+''.join([b[k*8:(k+1)*8][1:] for k in range(int(len(b)/8))]))
        if n == 0 and _rec: return 0
        self.writeVariable(n / 0x80, True)
        if _rec:
            self._buf += chr(n % 0x80 + 0x80)
        else:
            self._buf += chr(n % 0x80)

    def chEvent(self, dt, event, ch, p1, p2=-1):
        self.writeVariable(int(dt * timeDevision))
        self.writeFixed((event << 4) + ch, 1)
        self.writeFixed(p1, 1)
        if not p2 == -1:
            self.writeFixed(p2, 1)

    def metaEvent(self, dt, event, length, data):
        self.writeVariable(int(dt * timeDevision))
        self.writeFixed(0xff, 1)
        self.writeFixed(event, 1)
        self.writeVariable(length)
        self.writeFixed(data, length)

    def sysEx(self, dt, length, data):
        self.writeVariable(int(dt * timeDevision))
        self.writeFixed(0xf0, 1)
        self.writeVariable(length)
        self.writeFixed(data, length)

    def setTempo(self, bpm):
        # midi uses microsec/quarter note
        msqn = 60000000/bpm
        self.metaEvent(0, 0x51, 3, msqn)

    def noteOn(self, dt, ch, key, vol=1):
        self.chEvent(dt, 0x9, ch, key, int(vol * 0x7f))

    def noteOff(self, dt, ch, key, vol=1):
        self.chEvent(dt, 0x8, ch, key, int(vol * 0x7f))

    def lyrics(self, dt, s):
        self.metaEvent(dt, 0x05, len(s), s)

    def progCh(self, dt, ch, prog):
        self.chEvent(dt, 0xC, ch, prog)

    def ctrlEvent(self, dt, ctrl, v):
        self.chEvent(dt, 0xB, ch, ctrl, v)

    def setVol(self, dt, ch, vol=1):
        self.ctrlEvent(dt, ch, 0x07, int(vol * 0x7f))

class MidiFile(Midi):

    def __init__(self):
        Midi.__init__(self)
        self._tracks = []

    def update(self):
        self._buf = ''
        self.writeFixed(0x4D546864, 4) # chunk ID "MThd"
        self.writeFixed(6, 4) # chunk size
        self.writeFixed(1, 2) # format type
        self.writeFixed(len(self._tracks), 2) # numer of tracks
        self.writeFixed(timeDevision, 2) # time devision
        for track in self._tracks:
            self.writeFixed(0x4D54726B, 4) # chunk ID "MTtr"
            self.writeFixed(len(track._buf)+4, 4) # chunk size
            self._buf += track._buf
            self.metaEvent(0, 0x2f, 0, '') # endTrack event

    def addTrack(self, data, update=True):
        self._tracks.append(data)
        if update:
            self.update()

if __name__ == '__main__':
    # Example:
    f = MidiFile()
    f.addTrack(Midi())
    t = Midi()
    t.setVol(0, 1, 1)
    t.ctrlEvent(0, 1, 0x00, 0) # setting bank
    t.noteOn(0.5, 1, 60)
    t.noteOff(1, 1, 60)
    t.noteOn(0, 1, 62)
    t.noteOff(1, 1, 62)
    t.noteOn(0, 1, 64)
    t.noteOff(1, 1, 64)
    f.addTrack(t)
    print f
    f.write('test.mid')
