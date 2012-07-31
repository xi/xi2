#!/usr/bin/env python

from midi import *

"""
The tricky part here is the time conversion.
and noteOff events
"""

class IParser:
# creates midi events from intermediate code
# and than uses midi to create midi bytecode

	def __init__(self, seq, ch=0, offset=60):
		self.midi = Midi()
		self.ch = ch
		self.offset = offset
		self.dt = 0
		self.dtStack = []
		self.stack = []
		self.parseSeq(seq)

	def dtStep(self):
		a = 1.0
		for i in self.dtStack[1:]:
			a /= i
		return a	

	def parseEl(self, e):
		if e.isdigit(): # note
			self.midi.noteOn(self.dt, self.ch, self.offset+int(e), 1)
			self.dt = self.dtStep()
		elif e == '-': # continue
			self.dt += self.dtStep()
		elif e == '': # break
			self.dt += self.dtStep()
		else: # lyrics
			self.midi.lyrics(self.dt, e.replace('_', ' '))
			self.dt = self.dtStep()

	def parseSeq(self, seq):
		self.dtStack.append(len(seq))
		for e in seq:
			if type(e) == type(''):
				if e != '-': self.stop()
				self.stack.append(e)
				self.parseEl(e)
			elif type(e) == type([]):
				if not '-' in e: self.stop()
				self.stack.append(e)
				self.parseSet(e)
			elif type(e) == type(()):
				self.parseSeq(e)
			else:
				raise Exception("unknown element: " + e)
		self.dtStack.pop()

	def parseSet(self, s):
		for e in s:
			if type(e) != type(''):
				raise Exception("only elements are allowed inside sets: " + e)
			elif e == '':
				raise Exception("Breaks are not allowed inside sets!")
			else:
				self.parseEl(e)
			self.dt = 0
		self.dt = self.dtStep()

	def stop(self):
		if len(self.stack) == 0: return
		e = self.stack.pop()
		if type(e) == type(''):
			if e == '-':
				self.stop()
			elif e == '':
				pass # already stopped
			elif e.isdigit():
				self.midi.noteOff(self.dt, self.ch, self.offset+int(e), 1)
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
					self.midi.noteOff(self.dt, self.ch, self.offset+int(ee), 1)
					self.dt = 0
		else:
			raise Exception("Unexpected object on stack: " + e)

if __name__ == '__main__':
	a = [(('0', '1'), '2'), '4', '5', '-', '', ['0', '4', '7'], '', '', '0', ['3', '-']]

	f = MidiFile()
	ip = IParser(a, 0, 60)
	f.addTrack(ip.midi)
	f.write('test.mid')
