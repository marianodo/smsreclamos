import schedule
import serial
import time
import io
import re
import logging

logging.basicConfig(filename='smsReclamos.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logging.debug('This will get logged to a file')

PORT = "/dev/ttyUSB0"
BAUD = 115200
READ_ALL_MSG = "AT+CMGL=ALL" #Creo que es at+cmgf = "ALL", probar tambien con AT+CMGL=ALL
DEL_POS_MSG = "AT+CMGD=%s" #Investigar si es asi el comando para eliminar el msg en una posicion
class Modem(object):
	def __init__(self, port, baud):
		self.port = port
		self.baud = baud
		self.connection = None
		self.initModem()
		#self.open()

	def initModem(self):
		i = 0
		j = 0
		k = 0
		self.open()
		time.sleep(1)
		while i<3:
			self.connection.write('AT\r')			# Pregunto si el modem esta vivo
			time.sleep(1)
			atResp = self.connection.readlines(2)
			#print("Respuesta a AT\n")
			print(atResp)
			if(atResp[-1] == 'OK\r\n'):
				break
			time.sleep(1)
			i = i + 1

		while j<3:
			self.connection.write('AT+CMGF=1\r')		# Modem en modo texto
			time.sleep(1)
			cmgfResp = self.connection.readlines(2)
			#print ("Respuesta a CMGF\n")
			print (cmgfResp)
			if(cmgfResp[-1] == 'OK\r\n'):
				break
			time.sleep(1)
			j = j + 1

		while k<3:
			self.connection.write('AT+CSCS="IRA"\r')	# Para el modo texto, encoding tipo string
			time.sleep(1)
			csResp = self.connection.readlines(2)
			#print("Respuesta a CSCS\n")
			print(csResp)
			if(csResp[-1] == 'OK\r\n'):
				break
			time.sleep(1)
			k = k + 1

		self.connection.close()

	def open(self):
		self.connection = serial.Serial(self.port,  self.baud, timeout=3)
		#print (self.connection)

	def readMessage(self):
		rawData = []
		rawNumbers = []
		rawMsgs = []
		codes = []
		messages = []
		phoneNumbers = []
		wrongNumbers = []
		dataLines = 0
		msgLines = 0
		pattern = 0
		self.open()
		time.sleep(1)
		self.connection.write('AT+CMGL="ALL"\r')
		time.sleep(1)
		rawResponse = self.connection.readlines()

		rawResponse.pop(0)					# Elimino el primer elemento de la lista: CR y LF
		rawResponse.pop(-1)					# Elimino el ultimo elemento de la lista: OK


		for i in range(len(rawResponse)):			# Separo las lineas pares, que contienen el numero de remitente 
			if(i % 2 == 0):					# y otros datos, de las lineas impares, que contienen el mensaje
				rawData.append(rawResponse[i].split(','))
				dataLines = dataLines + 1
				#print(rawResponse[i])

			if(i % 2 != 0):
				rawMsgs.append(rawResponse[i])
				msgLines = msgLines + 1
				#print(rawResponse[i])

		for k in range(dataLines):
			rawNumbers.append(rawData[k][2])		# El tercer elemento ([2]) de cada lista que posee rawData 
									# es el numero. rawData es una lista de listas (Matriz)


		for l in range(msgLines):
			match = re.match(r"\d{4}",rawMsgs[l])		# Busco si el mensaje empieza con 4 digitos numericos
			if(match):
				codes.append(match.group())		# Si es asi guardo la coincidencia encontrada
				pattern = match.group()
				auxMsg = re.sub(pattern,'',rawMsgs[l])
				#print(auxMsg)
				messages.append(auxMsg.strip())			# Y guardo el mensaje correspondiente
				auxNumber = rawNumbers[l]
				phoneNumbers.append(auxNumber.strip('"'))

			else:
				auxNumber = rawNumbers[l]			# Si el formato del mensaje no es correcto
				wrongNumbers.append(auxNumber.strip('"'))	# guardo el numero del remitente en otra lista

		print("Codigo:", codes)
		print("Mensaje:", messages)
		print("Telefono:", phoneNumbers)
		print("Telefono error:", wrongNumbers)

		#return '0'

	def deleteMessage(self, position):
		self.connection.write(DEL_POS_MSG.format(position)) 



if __name__ == '__main__':
	modem = Modem(PORT, BAUD)

	def mainFun():
		print("Corriendo programa")

		newMsg = modem.readMessage()
                modem.connection.close()

	schedule.every(1).minutes.do(mainFun)
	#schedule.every().hour.do(job)
	#schedule.every().day.at("10:30").do(job)
	#schedule.every(5).to(10).days.do(job)
	#schedule.every().monday.do(job)
	#schedule.every().wednesday.at("13:15").do(job)



	while True: #Hacer esto si o si con un schedule, no con while true. Doc en https://pypi.org/project/schedule/

		schedule.run_pending()
    		time.sleep(1)


		#newMsg = modem.readMessage()
		#print('el mensaje nuevo es')
		#print(newMsg)
		#modem.connection.close()
		#print(newMsg)
		#logger.info(newMsg)
		#parserMessage(newMsg)

