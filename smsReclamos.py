# -*- coding: utf-8 -*-
import schedule
import serial
import sys
import time
import re
import logging
import json
import thread
import datetime
import unicodedata
import string
from dbSigesmen import Database

logging.basicConfig(filename='smsReclamos.log', filemode='a', format='%(asctime)s - %(message)s', level=logging.DEBUG)
logging.getLogger('schedule').propagate = False
DATABASE_FILE = "dbConf.json"
try:
    with open(DATABASE_FILE) as db:
            configFile = json.load(db)
    db = Database(configFile["user"], configFile["passwd"], configFile["host"], configFile["port"], configFile["database"])
except:
    logging.error("Error al abrir la BD. Revisar")
    sys.exit()

PORT = "COM5"
BAUD = 115200
IS_ALIVE = 'AT\r'
TEXT_MODE = 'AT+CMGF=1\r'
STRING_MODE = 'AT+CSCS="IRA"\r'
READ_ALL_MSG = 'AT+CMGL="ALL"\r'
DEL_MSG = 'AT+CMGD={0}\r'
ACK_MODEM = 'OK\r\n'
ERR = -1
TEST_CODE = 9999
ANSWER_TEST_CODE = 9998
ANSWER_TEST_MSG = "Recibido Test SMS {0}. {1}"
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
        print("Verificando Modem")
        isAliveCnt = 0
        #TODO Escribir en la BD si el modem no responde
        while isAliveCnt < 3:
            self.connection.write(IS_ALIVE)             # Pregunto si el modem esta vivo
            time.sleep(1)
            atResp = self.connection.readlines(2)
            if(atResp[-1] == ACK_MODEM):
                break
            time.sleep(1)
            isAliveCnt += 1
    
    def modemTextMode(self):
        print("Configurando Modo Texto")
        textConfigCnt = 0
        #TODO Escribir en la BD por si no se pudo configurar el Modem
        while textConfigCnt < 3:
            self.connection.write(TEXT_MODE)            # Modem en modo texto
            time.sleep(1)
            cmgfResp = self.connection.readlines(2)
            if(cmgfResp[-1] == ACK_MODEM):
                break
            time.sleep(1)
            textConfigCnt += 1

    def modemStringMode(self):
        print("Configurando Modo String")
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
        rawResponse.pop(0) # Elimino el primer elemento de la lista ("\r\n")
        rawResponse.pop(-1) # Elimino el ultimo elemento de la lista ("OK\r\n")
        return rawResponse

    def deleteMessageAtPosc(self, posc):
        self.open()
        time.sleep(1)
        self.connection.write(DEL_MSG.format(posc))
        self.connection.close()

class Parser(object):
    def parseMessage(self, rawMessage):
        
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
            try:
                    dataMsg = rawMessage[pos + 1]
            except:
                    print rawMessage
                    print "ERROR"
                    pass
            if "REC READ" in rawMessage[pos] or "REC UNREAD" in rawMessage[pos]:
                logging.info(rawMessage[pos])
                logging.info(dataMsg)
                posId, phone = self.parseMetadata(rawMessage[pos])
                code, message = self.parseMsg(dataMsg)

                if code != ERR:
                        if code == '9999':
                                answerTest = ANSWER_TEST_MSG.format(message.split()[-1], phone)
                                print "Respondiendo TEST " + answerTest
                                db.sendMessage(ANSWER_TEST_CODE, answerTest)
                        else:
                                if db.isCodeExists(code):
                                        print "Mensaje correcto. Enviando mensaje"
                                        db.sendMessage(code, "{0}. Enviado por: {1}".format(message, phone))
                                        db.answerCustomer(ANSWER_TO_CUSTOMER.format(code), phone)
                                else:
                                        print "Codigo no existe. Respondiando al usuario"
                                        db.answerCustomer(BAD_CODE.format(code), phone)
                else:
                        print "Mensaje invalido, respondiendo al usuario"
                        logging.warning("Mensaje Invalido: {0}".format(dataMsg))
                        db.answerCustomer(INVALID_FORMAT, phone)

                print rawMessage[pos + 1]

        
    def parseMetadata(self, data):
                try:
                        #data = '"+CMGL: 0,"REC READ","+543513162097",,"18/10/02,19:10:15-12"\r\n'
                        parsedMeta = data.split(",")
                        #parsedMeta = ['+CMGL: 0', '"REC READ"', '"+543513162097"', '', '"18/10/02', '19:10:15-12"\r\n']
                        posId = parsedMeta[0].split(" ")[1].strip('"')
                        phone = (parsedMeta[2]).strip('"')
                        return posId, phone
                except:
                        logging.warning("Formato invalido - {0}".format(data))
                        return 0

    def getMessagePosition(self, msg):
        #data = '"+CMGL: 0,"REC READ","+543513162097",,"18/10/02,19:10:15-12"\r\n'
        parsedMeta = msg.split(",")
        return parsedMeta[0].split(" ")[1].strip('"')

    def getMessagePhone(self, msg):
        #data = '"+CMGL: 0,"REC READ","+543513162097",,"18/10/02,19:10:15-12"\r\n'
        parsedMeta = msg.split(",")
        return parsedMeta[2].strip('"')

    def getMessage(self, data):
        #data = '3407 Dirigirse a Rivadeo 1486 por ascensor fuera de servicio'
        match = re.match(r"\d{4}",data.strip()) # Busco si el mensaje empieza con 4 digitos numericos
        if(match):
            code = match.group() # Si es asi guardo la coincidencia encontrada
            message = (re.sub(code,'',data)).strip()
            return code, message
        else:   
            logging.warning("Formato invalido")     
            return ERR, INVALID_FORMAT


    def parseMsg(self, data):
        #data = '3407 Dirigirse a Rivadeo 1486 por ascensor fuera de servicio'
        match = re.match(r"\d{4}",data.strip()) # Busco si el mensaje empieza con 4 digitos numericos
        if(match):
            code = match.group() # Si es asi guardo la coincidencia encontrada
            message = (re.sub(code,'',data)).strip()
            return code, message
        else:   
            logging.warning("Formato invalido")     
            return ERR, INVALID_FORMAT

if __name__ == '__main__':
    print("Iniciando programa")
    modem = Modem(PORT, BAUD)
    parser = Parser()

    def mainFun():
        rawMessage = modem.readMessage()
        for pos in xrange(0, len(rawMessage), 2):
            try:
                    metadata = rawMessage[pos]
                    dataMsg = rawMessage[pos + 1]
            except:
                    print rawMessage
                    print "ERROR"
                    pass
            if "REC READ" in metadata or "REC UNREAD" in metadata:
                posId = parser.getMessagePosition(metadata)
                phone = parser.getMessagePhone(metadata)
                code, message = parser.getMessage(dataMsg)

                if code != ERR:
                    if code == '9999':
                        answerTest = ANSWER_TEST_MSG.format(message.split()[-1], phone)
                        print "Respondiendo TEST " + answerTest
                        db.sendMessage(ANSWER_TEST_CODE, answerTest)
                    elif db.isCodeExists(code):
                        print "Mensaje correcto. Enviando mensaje"
                        db.sendMessage(code, "{0}. Enviado por: {1}".format(message, phone))
                        db.answerCustomer(ANSWER_TO_CUSTOMER.format(code), phone)
                    else:
                        print "Codigo no existe. Respondiando al usuario"
                        db.answerCustomer(BAD_CODE.format(code), phone)
                else:
                        print "Mensaje invalido, respondiendo al usuario"
                        logging.warning("Mensaje Invalido: {0}".format(dataMsg))
                        db.answerCustomer(INVALID_FORMAT, phone)
                print dataMsg
                modem.deleteMessageAtPosc(posId)



    def printDatetime():
        while True:
            sys.stdout.write('%s\r' % datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S'))
            sys.stdout.flush()
            time.sleep(1)

    thread.start_new_thread(printDatetime, ())
    schedule.every(10).seconds.do(mainFun)

    while True:
        schedule.run_pending()
