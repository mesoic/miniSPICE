# ---------------------------------------------------------------------------------
# 	minispice -> freqAnalysis.py
#	Copyright (C) 2020 Michael Winters
#	github: https://github.com/mesoic
#	email:  mesoic@protonmail.com
# ---------------------------------------------------------------------------------
#	
#	Permission is hereby granted, free of charge, to any person obtaining a copy
#	of this software and associated documentation files (the "Software"), to deal
#	in the Software without restriction, including without limitation the rights
#	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#	copies of the Software, and to permit persons to whom the Software is
#	furnished to do so, subject to the following conditions:
#	
#	The above copyright notice and this permission notice shall be included in all
#	copies or substantial portions of the Software.
#	
#	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#	SOFTWARE.
#

# Classes for array manipulation
import numpy as np
import collections
import math
import copy
import re

# For plotting
import matplotlib.pyplot as plt

# Imprt node matrix
from .nodeMatrix import nodeMatrix
from .Converter import *

# Class to construct y-matrix for a list of frequencies
class freqAnalysis: 
	
	# Method to initialize directly
	def __init__(self, data, freq, components):

		# Data is dict of admittance matrices
		self.data = data

		# List of frequencies to simulate
		self.freq = freq
		
		# Dictionary to hold components
		self.components = components
	
	# Overload constructor via @classmethod	
	@classmethod
	def fromFile(cls, path, freq):
	
		# Read all components into dict
		components = {}

		# While parsing, we will determine the size of admittace matrix
		size = 0

		with open(path, 'r') as f:
		
			for _line in f:

				# Split component data
				_comp = _line.split()

				# Extract nodes from list
				_nodes = [ int(n) for n in _comp[1:len(_comp)-1] ]

				# Augment size if necessary
				if max(_nodes) > size:
					size = max(_nodes)

				# Parse data into dictionary 
				try:
					components[ _comp[0] ] = {"nodes" : _nodes, "value" : float(_comp[-1]) }

				except:
					components[ _comp[0] ] = {"nodes" : _nodes, "value" : str(_comp[-1]) }

		# Create a dictionary for admittance matrices
		data = collections.OrderedDict()
				
		# Loop through frequencies and initialize components
		for f in freq:

			# Initialize node matrix for frequency f
			ymatrix = nodeMatrix(size, f)
		
			# Loop through components and add them in
			for _comp, _conf in components.items():

				# Passive components
				if re.match(r'R|C|L', _comp) is not None:
	
					ymatrix.addPassive(
						_comp, 
						_conf["nodes"][0], 
						_conf["nodes"][1], 
						_conf["value"]
					)

				# Transistor with model file
				elif re.match(r'Q', _comp) is not None: 
					
					ymatrix.addTransistor(
						_comp, 
						_conf["nodes"][0], 
						_conf["nodes"][1], 
						_conf["nodes"][2], 
						_conf["value"]
					)

				# Case of a VCCS (transconductance)			
				elif re.match(r'G', _comp) is not None:
					
					ymatrix.addVCCS(
						_comp, 
						_conf["nodes"][0], 
						_conf["nodes"][1], 
						_conf["nodes"][2], 
						_conf["nodes"][3], 
						_conf["value"]
					)

				# Pass 
				else:
					pass

			# Assign data 
			data[f] = ymatrix
			
		return cls(data, freq, components)

	# Method to return S-parameters for two nodes over all frequencies
	def Sparameters(self, n1, n2):

		sdata = collections.OrderedDict()

		for f, ymatrix in self.data.items(): 
		
			sdata[f] = ytos( ymatrix.toTwoport(n1,n2) )	

		return sdata	

	# Return a single matrix from simulation
	def getMatrix(self, freq ):
		return self.data[ freq ] if freq in self.data.keys() else None

	# Method to return entire data structure	
	def getData(self):
		return self.data

	# Methods to return abs and angle of list
	def abs(self, _data):
		return [ np.abs(_) for _ in _data ]

	def angle(self, _data):
		return [ np.angle(_) for _ in _data ]	

	# Calculate voltage gain between two nodes in node admittance matrix
	def calcVoltageGain(self, n1, n2):	
		return [ self.data[f].voltageGain(n1, n2) for f, ymatrix in self.data.items() ]

	# Calculate gain of effective twoport network connected to Rs and Rl
	def calcNetworkGain(self, n1, n2, Zs, Zl):
		return [ np.abs( self.data[f].networkGain(n1, n2, Zs, Zl) ) for f, ymatrix in self.data.items() ]

	# Calculate input impedance
	def calcInputImpedance(self, n1, n2, Zl):	
		return [ self.data[f].inputImpedance(n1, n2, Zl) for f, ymatrix in self.data.items() ]

	# Calculate output impedance
	def calcOutputImpedance(self, n1, n2, Zs):	
		return [ self.data[f].outputImpedance(n1, n2, Zs) for f, ymatrix in self.data.items() ]
	