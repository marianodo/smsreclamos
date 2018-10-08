import schedule
import serial
import time
import re
import logging

logging.basicConfig(filename='smsReclamos.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logging.debug('This will get logged to a file')

PORT = "/dev/ttyUSB0"
BAUD = 115200
READ_ALL_MSG = 'AT+CMGL="ALL"'
DEL_POS_MSG = 'AT+CMGD=1,4'

class Modem(object):
	def __init__(self, port, baud):
		self.port = port
		self.baud = baud
		self.connection = None
		self.initModem()

	def initModem(self):
		i = 0
		j = 0
		k = 0
		self.open()
		time.sleep(1)
		while i < 3:
			self.connection.write('AT\r')				# Pregunto si el modem esta vivo
			time.sleep(1)
			atResp = self.connection.readlines(2)
			if(atResp[-1] == 'OK\r\n'):
				break
			time.sleep(1)
			i = i + 1

		while j < 3:
			self.connection.write('AT+CMGF=1\r')		# Modem en modo texto
			time.sleep(1)
			cmgfResp = self.connection.readlines(2)
			if(cmgfResp[-1] == 'OK\r\n'):
				break
			time.sleep(1)
			j = j + 1

		while k < 3:
			self.connection.write('AT+CSCS="IRA"\r')	# Para el modo texto, encoding tipo string
			time.sleep(1)
			csResp = self.connection.readlines(2)
			if(csResp[-1] == 'OK\r\n'):
				break
			time.sleep(1)
			k = k + 1

		self.connection.close()

	def open(self):
		self.connection = serial.Serial(self.port,  self.baud, timeout=3)

	def readMessage(self):
		
		self.open()
		time.sleep(1)
		self.connection.write('AT+CMGL="ALL"\r')
		time.sleep(1)
		rawResponse = self.connection.readlines()
		self.connection.close()
		logging.info(rawResponse)
		return rawResponse

	def parseMessage(self, rawMessage):

		def parseMetadata(data):
			#data = '"+CMGL: 0,"REC READ","+543513162097",,"18/10/02,19:10:15-12"\r\n'
			parsedMeta = data.split(",")
			#parsedMeta ['+CMGL: 0', '"REC READ"', '"+543513162097"', '', '"18/10/02', '19:10:15-12"\r\n']
			phone = (parsedMeta[2]).strip('"')
			
			return phone


		def parseMsg(data):
			#data = '3407 Dirigirse a Rivadeo 1486 por ascensor fuera de servicio'
	
			match = re.match(r"\d{4}",data.strip())				# Busco si el mensaje empieza con 4 digitos numericos
		
			if(match):
				code = match.group()							# Si es asi guardo la coincidencia encontrada
				message = (re.sub(code,'',data)).strip()
				return code, message

			else:	
				logging.warning("Formato invalido")		
				return -1, "Error, formato no valido"	

		def deleteMessage(self):
			
			self.open()
			time.sleep(1)
			self.connection.write('AT+CMGD=1,4') 
			self.connection.close()


		rawMessage.pop(0)
		rawMessage.pop(-1)

		'''
		['+CMGL: 0,"REC READ","+543513162097",,"18/10/02,19:10:15-12"\r\n', 
		'3407 Dirigirse a Rivadeo 1486 por ascensor fuera de servicio\r\n', '+CMGL: 1,"REC READ","22123",,
		"18/10/02,15:29:03-12"\r\n', 'Telegram code 59896\r\n', '+CMGL: 2,"REC READ","+543517501403",,
		"18/10/02,07:48:01-12"\r\n', 'El nro. 3517501403  llamo el 02/10 07:47  Para llamarlo, presiona SEND.\r\n',
		'+CMGL: 3,"REC READ","+543516692434",,"18/10/02,17:52:47-12"\r\n', 'El nro. 3516692434  llamo el 02/10 17:52
		Para llamarlo, presiona SEND.\r\n', '+CMGL: 4,"REC READ","+543512482435",,"18/10/02,19:17:37-12"\r\n', 
		'El nro. 3512482435  llamo el 02/10 19:17  Para llamarlo, presiona SEND.\r\n', '+CMGL: 5,"REC READ","+543513024522"
		,,"18/10/02,19:37:45-12"\r\n', 'El nro. 3513024522  llamo el 02/10 19:37  Para llamarlo, presiona SEND.\r\n', 
		'+CMGL: 6,"REC READ","22123",,"18/10/02,23:24:26-12"\r\n', 'Telegram code 95705\r\n', '+CMGL: 7,"REC READ",
		"+543513998344",,"18/10/01,23:30:31-12"\r\n', '9999 PRUEBA TEST SMS (79549)\r\n', '+CMGL: 8,"REC READ",
		"+543513998344",,"18/10/02,00:00:13-12"\r\n', '9999 PRUEBA TEST SMS (79550)\r\n', '+CMGL: 9,"REC READ",
		"+543513998344",,"18/10/02,00:30:43-12"\r\n', '9999 PRUEBA TEST SMS (79551)\r\n', '+CMGL: 10,"REC READ",
		"+543515073753",,"18/10/02,01:00:34-12"\r\n', '9999 PRUEBA TEST SMS (79552)\r\n', '+CMGL: 11,"REC READ",
		"+543513998344",,"18/10/02,01:30:42-12"\r\n', '9999 PRUEBA TEST SMS (79553)\r\n', '+CMGL: 12,"REC READ",
		"+543515073753",,"18/10/02,02:00:18-12"\r\n', '9999 PRUEBA TEST SMS (79554)\r\n', '+CMGL: 13,"REC READ",
		"+543513998344",,"18/10/02,02:30:25-12"\r\n', '9999 PRUEBA TEST SMS (79555)\r\n', '+CMGL: 14,"REC READ",
		"+543515073753",,"18/10/02,03:00:31-12"\r\n', '9999 PRUEBA TEST SMS (79556)\r\n']
		'''

		for pos in xrange(0, len(rawMessage), 2):
			phone = parseMetadata(rawMessage[pos])
			code, message = parseMsg(rawMessage[pos + 1])
			print(phone)
			print(code,message)



		#self.deleteMessage()



if __name__ == '__main__':
	modem = Modem(PORT, BAUD)

	#def mainFun():
		#print("Corriendo programa")

		#newMsg = modem.readMessage()

       	#modem.parseMessage(newMsg)


	#schedule.every(1).minutes.do(mainFun)

	while True:

		#schedule.run_pending()
    	#time.sleep(1)
		print("Corriendo programa")

		newMsg = modem.readMessage()
		modem.parseMessage(newMsg)


