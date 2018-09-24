import serial
import time
PORT = ""
BAUD = ""
READ_ALL_MSG = "AT+CMGF=ALL" #Creo que es at+cmgf = "ALL"
DEL_POS_MSG = "AT+CMGD=%s" #Investigar si es asi el comando para eliminar el msg en una posicion
class Modem(object):
	def __init__(self, port, baud):
		self.port = port
		self.baud = baud
		self.connection = None
		self.open()

	def open(self):
		self.connection = serial.Serial("/dev/ttyACM0",  460800, timeout=5)

	def readMessage(self):
		self.connection.write(READ_ALL_MSG) 
		time.sleep(1) #siempre hay que esperar uno o dos segundos.
		return self.connection.read()

	def deleteMessage(self, position):
		self.connection.write(DEL_POS_MSG.format(position)) 



if __name__ == '__main__':
	modem = Modem(PORT, BAUD)
	while True: #Hacer esto si o si con un schedule, no con while true. Doc en https://pypi.org/project/schedule/
		newMsg = modem.readMessage()
		logger.info(newMsg)

