#!/usr/bin/env python

# Raspberry Pi 3 B 
# MCP3208 8 channel 12 bit SPI A2D converter
# Demo by D. Scott Williamson, 2017
# This code and documentation is provided without warranty, 
# use code and instructions at your own risk.

# MCP3208 Datasheet can be found here:
# http://ww1.microchip.com/downloads/en/devicedoc/21298c.pdf

# To enable SPI on your Raspberry Pi
# 	Run Raspberry Pi Configuration from the Preferences menu, 
# 	select Interfaces tab and enable SPI

# List SPI ports: 
# 	ls -l /dev/spidev*
# 	You should see this:
#		crw-rw---- 1 root spi 153, 0 Jan 22 17:52 /dev/spidev0.0
#		crw-rw---- 1 root spi 153, 1 Jan 22 17:52 /dev/spidev0.1

# Electrical connections
# Required:
#	Power:
#		Connect MCP3208 pin 16 VDD to GPIO header pin 1 (3.3v or any other 3.3v)
#		Connect MCP3208 pin 9 DGND to GPIO header pin 9 (GND or any other GND)
#	SPI:
#		Connect MCP3208 pin 10 -CS/SHDN GPIO header pin 24 (SPI_CE0_N GPIO8)
#			This will enable the chip as chip "0" to the Pi if 2 are on the bus
#		Connect MCP3208 pin 11 Din to GPIO header pin 19 (SPI_MOSI GPIO10)
#			MOSI: "Master Out Slave In" connected to Din: Data in on the slave
#		Connect MCP3208 pin 12 Dout to GPIO header pin 21 (SPI_MISO GPIO9)
#			MISO: "Master In Slave Out" connected to Dout: Data out on the slave
#		Connect MCP3208 pin 13 CLK to GPIO header pin 23 (SPI0_CLK GPIO11)
#			Clock that only the master (Pi) generates for all communication

# Optional analog inputs:
# 	Connect MCP3208 pin 15 Vref to MCP3208 pin 16 Vdd for this sample
#		This is the analog reference voltage, i.e. value "4095"
# 	Connect MCP3208 pin 14 Agnd to MCP3208 pin 9 GND for this sample
#		This is the analog ground, i.e. value "0" 
# 	Connect a potentiometer (any value between 1k and 10k will be fine)
# 		Connect power across the potentiometer (the two pins that measure 
#			the most resistance while the wiper is in the middle)
# 		One leg to GND, GPIO header pin 9 (or one of the other GND pins).
#		Oppsite leg to 3.3v GPIO header pin 1 (or one of the other 3.3v pins)
#		Connect the wiper, usually the center pin, to an analog input
#	Connect any analog input to 3.3v or GND

################################################################################
#
# Imports
#
import time	# used for sleep function
import sys		# used for print function
import spidev	# used to access SPI bus

################################################################################
#
# Variables
#

# Get access to the SPI bus
spi = spidev.SpiDev()

# Configuration bits for the MCP3208

# start bit for communication
START_BIT = 0x10

# Configure the inputs
# differential configurations (measurements between inputs)
CONFIG_DIFFERENTIAL_AN0_P_AN1_N	= 0X00
CONFIG_DIFFERENTIAL_AN1_P_AN0_N	= 0X01
CONFIG_DIFFERENTIAL_AN2_P_AN3_N	= 0X02
CONFIG_DIFFERENTIAL_AN3_P_AN2_N	= 0X03
CONFIG_DIFFERENTIAL_AN4_P_AN5_N	= 0X04
CONFIG_DIFFERENTIAL_AN5_P_AN4_N	= 0X05
CONFIG_DIFFERENTIAL_AN6_P_AN7_N	= 0X06
CONFIG_DIFFERENTIAL_AN7_P_AN6_N	= 0X07
# single ended configurations (measurement between an input and ground)
CONFIG_SINGLE_ENDED_AN0_P_GND_N	= 0X08
CONFIG_SINGLE_ENDED_AN1_P_GND_N	= 0X09
CONFIG_SINGLE_ENDED_AN2_P_GND_N	= 0X0A
CONFIG_SINGLE_ENDED_AN3_P_GND_N	= 0X0B
CONFIG_SINGLE_ENDED_AN4_P_GND_N	= 0X0C
CONFIG_SINGLE_ENDED_AN5_P_GND_N	= 0X0D
CONFIG_SINGLE_ENDED_AN6_P_GND_N	= 0X0E
CONFIG_SINGLE_ENDED_AN7_P_GND_N	= 0X0F


################################################################################
#
# Functions
#

# Read a 12 bit analog value from one of the 8 channels
def readAdc(channel):
	# sanity check the channel specified
	if ((channel > 7) or (channel < 0)):
		return -1
		
 	# On SPI, since there are two data lines, input and output between the 
	# master and the slave can happen at the same time on the same clocks.
	# Only the master, the Raspberry Pi generates the the clock signals.
	#
	# The MCP3208 requires a start bit followed by 4 control bits, then a
	# 2 bit delay while it captures and reads the analog value, then it sends
	# the 12 bit analog value back to the master.
	# Careful bit timing is used to issue the read command and receive the 
	# 12 bit analog value within 24 bits (3 bytes).
	# 
	# The communication looks like this: 
	#	Output: 00000SCC CCRR0000 00000000
	#	Input:  00000000 0000HHHH LLLLLLLL
	# Where:
	#	S is the start bit
	#	C are the 4 configuration bits
	#	R is the 2 bit time it takes to capture and read the analog value
	#	H is the high 4 bits of the analog value
	# 	L is the low 8 bits of the analog value

	# build read command
	config=(START_BIT |							# Start bit
			CONFIG_SINGLE_ENDED_AN0_P_GND_N |	# Single ended read of AN0 
			channel)								# Analog channel to read 

	# create array of 3 carefully timed bytes to be sent 
	# (per the above explanation)
	sendBytes = [	(config>>2) & 0x07,
					(config<<6) & 0xC0,
					0	]      
	
	# send array of bytes over the SPI bus, 
	# bytes read on the same clock signals are returned in an array
	rcvBytes = spi.xfer2(sendBytes)

	# combine 4 high bits with 8 low bits 
	value = ((rcvBytes[1] & 0x0f) << 8) | rcvBytes[2] 

	# return the value
	return value

# program entry
if __name__ == '__main__':
	print "=========================================================="
	print "Raspberry Pi 3 b"
	print "MCP3208 8 channel 12 bit SPI A2D converter demo"
	print "by D. Scott Williamson, 2017"
	print "This code and documentation is provided without warranty."
	print "Use at your own risk."
	print "=========================================================="
	time.sleep(3)
	try:
		# Open spi bus 0 device 0
		# Pi only has 1 bus, "0"
		# Device 0 is enabled by pin SPI_CE0_N, GPIO8 on the header pin 24
 		spi.open(0,0)
 		
		# loop and display analog values
		while True:
			s="Ctrl-C to exit, ADC: "
			for i in range(0,8):
				val = readAdc(i)
				s+=str(i)+":"+str(val).zfill(4)+" "
			print s
			time.sleep(0.05)
			
	except KeyboardInterrupt:
		# capture keyboard interrupt (Ctrl-C) to exit cleanly
		# release the SPI bus
		spi.close() 
		# exit
		sys.exit(0)
