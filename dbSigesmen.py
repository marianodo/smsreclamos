import MySQLdb

USER = "root"
PASS = "root"
HOST = "192.168.1.7"
PORT = 3306
DATABASE = "sigesmen"

INSERT_MESSAGE = "INSERT INTO bla() VALUES(%s,%s)"
GET_CLIENT = "SELECT id FROM bla WHERE code = %s"

class Database(object):
	__instance   = None
    __host       = None
    __user       = None
    __password   = None
    __database   = None
    __session    = None
    __connection = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance or not cls.__database:
             cls.__instance = super(MysqlPython, cls).__new__(cls,*args,**kwargs)
        return cls.__instance
    ## End def __new__

    def __init__(self):
        self.__host     = HOST
        self.__user     = USER
        self.__password = PASS
        self.__database = DATABASE
    ## End def __init__

    def __open(self):
        try:
            cnx = MySQLdb.connect(self.__host, self.__user, self.__password, self.__database)
            self.__connection = cnx
            self.__session    = cnx.cursor()
        except MySQLdb.Error as e:
            print "Error %d: %s" % (e.args[0],e.args[1])
    ## End def __open

    def __close(self):
        self.__session.close()
        self.__connection.close()
    ## End def __close
	
	def isCodeExists(self, code):
        self.__open()
        self.__session.execute(query, values)
		self.cursor.execute(GET_CLIENT.format(code))
		
	def __enter__(self):
		return self

	def __exit__(self, ext_type, exc_value, traceback):
		self.cursor.close()
		if isinstance(exc_value, Exception):
			self.connection.rollback()
		else:
			self.connection.commit()
		self.connection.close()