import schedule
import serial
import sys
import time
import re
import logging
import json
from dbSigesmen import Database

logging.basicConfig(filename='smsReclamos.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

DATABASE_FILE = "dbConf.json"
try:
	with open(DATABASE_FILE) as db:
		    configFile = json.load(db)
	db = Database(configFile["user"], configFile["passwd"], configFile["host"], configFile["port"], configFile["database"])
except:
	logger.error("Error al abrir la BD. Revisar")
	sys.exit()
PORT = "/dev/ttyUSB0"
BAUD = 115200
IS_ALIVE = 'AT\r'
TEXT_MODE = 'AT+CMGF=1\r'
STRING_MODE = 'AT+CSCS="IRA"\r'
READ_ALL_MSG = 'AT+CMGL="ALL"\r'
DEL_ALL_MSG = 'AT+CMGD=1,4\r'
ACK_MODEM = 'OK\r\n'
ERR = -1
INVALID_FORMAT = 'Respuesta Automatica. Mensaje Incorrecto. Recuerde que es codigo o clave y luego el mensaje que desee. Muchas Gracias'
BAD_CODE = "El codigo {0} no pertence a nuestra base de datos."
ANSWER_TO_CUSTOMER = "Su mensaje a la clave: {0} se ha enviado correctamente. Muchas gracias"
class Modem(object):
	def __init__(self, port, baud):
		self.port = port
		self.baud = baud
		self.connection = None
		self.initModem()

	def initModem(self):
		self.open()
		time.sleep(1)
		self.isModemAlive()
		self.modemTextMode()
		self.modemStringMode()
		self.connection.close()

	def isModemAlive(self):
		isAliveCnt = 0
		#TODO Escribir en la BD si el modem no responde
		while isAliveCnt < 3:
			self.connection.write(IS_ALIVE)				# Pregunto si el modem esta vivo
			time.sleep(1)
			atResp = self.connection.readlines(2)
			if(atResp[-1] == ACK_MODEM):
				break
			time.sleep(1)
			isAliveCnt += 1
	
	def modemTextMode(self):
		textConfigCnt = 0
		#TODO Escribir en la BD por si no se pudo configurar el Modem
		while textConfigCnt < 3:
			self.connection.write(TEXT_MODE)			# Modem en modo texto
			time.sleep(1)
			cmgfResp = self.connection.readlines(2)
			if(cmgfResp[-1] == ACK_MODEM):
				break
			time.sleep(1)
			textConfigCnt += 1

	def modemStringMode(self):
		stringConfigCnt = 0
		#TODO Escribir en la BD por si no se pudo configurar el Modem
		while stringConfigCnt < 3:
			self.connection.write(STRING_MODE) # Para el modo texto, encoding tipo string
			time.sleep(1)
			csResp = self.connection.readlines(2)
			if(csResp[-1] == ACK_MODEM):
				break
			time.sleep(1)
			stringConfigCnt += 1
	
	def open(self):
		self.connection = serial.Serial(self.port,  self.baud, timeout=3)

	def readMessage(self):
		self.open()
		time.sleep(1)
		self.connection.write(READ_ALL_MSG)
		time.sleep(1)
		rawResponse = self.connection.readlines()
		self.connection.close()
		logging.info(rawResponse)
		return rawResponse

	def deleteAllMessages(self):
		self.open()
		time.sleep(1)
		self.connection.write(DEL_ALL_MSG)
		self.connection.close()

class Parser(object):
	def parseMessage(self, rawMessage):
		rawMessage.pop(0) # Elimino el primer elemento de la lista ("\r\n")
		rawMessage.pop(-1) # Elimino el ultimo elemento de la lista ("OK\r\n")
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
		"+543513998344",,"18/10/02,02:30:25-12"\r\n', '9999 PRUEBA TEST SMS (79555)\r\n', '+CMGL: 14,"REC READ",
		"+543515073753",,"18/10/02,03:00:31-12"\r\n', '9999 PRUEBA TEST SMS (79556)\r\n']
		'''
		for pos in xrange(0, len(rawMessage), 2):
			phone = self.parseMetadata(rawMessage[pos])
			code, message = self.parseMsg(rawMessage[pos + 1])

			if code != 9999:
				if code != ERR:
					if db.isCodeExists(code):
						db.sendMessage(code, "{0}. Enviado por: {1}".format(message, phone))
						db.answerCustomer(ANSWER_TO_CUSTOMER.format(code), phone)
					else:
						db.answerCustomer(BAD_CODE.format(code), phone)
				else:
					db.answerCustomer(INVALID_FORMAT, phone)

	def parseMetadata(self, data):
		#data = '"+CMGL: 0,"REC READ","+543513162097",,"18/10/02,19:10:15-12"\r\n'
		parsedMeta = data.split(",")
		#parsedMeta = ['+CMGL: 0', '"REC READ"', '"+543513162097"', '', '"18/10/02', '19:10:15-12"\r\n']
		phone = (parsedMeta[2]).strip('"')
		return phone

	def parseMsg(self, data):
		#data = '3407 Dirigirse a Rivadeo 1486 por ascensor fuera de servicio'
		match = re.match(r"\d{4}",data.strip())	# Busco si el mensaje empieza con 4 digitos numericos
		if(match):
			code = match.group() # Si es asi guardo la coincidencia encontrada
			message = (re.sub(code,'',data)).strip()
			return code, message
		else:	
			logging.warning("Formato invalido")		
			return ERR, INVALID_FORMAT

if __name__ == '__main__':
	modem = Modem(PORT, BAUD)
	parser = Parser()

	def mainFun():
		print("Corriendo programa")
		newMsg = modem.readMessage()
		parser.parseMessage(newMsg)
		modem.deleteAllMessages()

	schedule.every(10).seconds.do(mainFun)

	while True:
		schedule.run_pending()
