# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import socket
import os
from constants import *
from base64 import b64encode
import logging

class Connection(object):
    """
    Conexión punto a punto entre el servidor y un cliente.
    Se encarga de satisfacer los pedidos del cliente hasta
    que termina la conexión.
    """

    def __init__(self, socket, directory):
        # FALTA: Inicializar atributos de Connection
        self.socket = socket
        self.directory = directory
        self.connect = True
        self.buffer = ""

    def valid_file(self, filename: str):
        """
        Returns:
            CODE_OK si el archivo existe y es valido.
            INVALID_ARGUMENTS si el nombre del archivo no es valido.
            FILE_NOT_FOUND si el archivo no existe.
        """
        # Obtiene los caracteres del nombre del archivo que no pertenecen a VALID_CHARS
        aux = set(filename) - VALID_CHARS
        if os.path.isfile(os.path.join(self.directory, filename)) and len(aux) == 0:
            return CODE_OK
        elif len(aux) != 0:
            return INVALID_ARGUMENTS
        else:
            return FILE_NOT_FOUND
    
    def send(self, message, codif = "ascii"):
        """
        Envia un mensaje a través del socket de la conexión.

        Args:
            msj: Mensaje a enviar, puede ser una cadena de texto o bytes.
            codif: Codificación a utilizar para enviar el mensaje. Por defecto es "ascii".

        Raises:
            ValueError: Si se especifica una codificación inválida.
        """
        try:
            # Verifica y aplica la codificación a utilizar
            if codif == "ascii":
                message = message.encode("ascii")
            elif codif == "b64encode":
                message = b64encode(message)
            else:
                raise ValueError(f"send: codificación inválida '{codif}'")
            # Envía el mensaje
            while message:
                bytes_sent = self.socket.send(message)
                assert bytes_sent > 0
                message = message[bytes_sent:]
            self.socket.send(EOL.encode("ascii"))  # Envía el fin de línea

        except BrokenPipeError or ConnectionResetError:
            logging.warning("No se pudo contactar al cliente")
            self.connect = False
        
        
    def error_handler(self, cod: int):
        """
        Envia el encabezado de respuesta al cliente y
        cierra la conexión en los errores fatales.

        Args:
            cod: Código de respuesta a enviar.
        """
        if fatal_status(cod):
            self.send(f"{cod} {error_messages[cod]}")
            self.quit()
        else:
            self.send(f"{cod} {error_messages[cod]}")
        
        
    def quit(self):
        """
        Cierra la conexión al cliente
        """
        self.send(f"{CODE_OK} {error_messages[CODE_OK]}")
        self.connect = False
        

        
    def get_file_listing(self):
        """
        Obtiene la lista de archivos disponibles en el directorio y la envía al cliente
        """
        rta = ""
        # Itero sobre la lista de archivos disponibles en el directorio
        for fil in os.listdir(self.directory):
            # Agrego los archvios a la cadena de respuesta
            rta += fil + EOL
        self.error_handler(CODE_OK)
        self.send(rta)
      
                
    def get_metadata(self, filename):
        """
        Devuelve un diccionario con los metadatos del archivo filename.
        """
        aux = set(filename) - VALID_CHARS
        if os.path.isfile(os.path.join(self.directory, filename)) and len(aux) == 0:
            file_size = os.path.getsize(os.path.join(self.directory, filename))
            self.error_handler(CODE_OK)
            self.send(f"{file_size}")
        elif len(aux) != 0:
            self.error_handler(INVALID_ARGUMENTS)    
        else:
            self.error_handler(FILE_NOT_FOUND)
            
    
    def get_slice(self, filename: str, offset: int, size: int):
        """
        Args:
            filename (str): El nombre del archivo del que se va a obtener el slice.
            offset (int): El byte de inicio del slice.
            size (int): El tamaño del slice.
        """
        # Se verifica si es un archivo valido
        if self.valid_file(filename) != CODE_OK:
            # Se envia el mensaje de error correspondiente por no ser un archivo valido
            self.error_handler(self.valid_file(filename))
        else:
            filepath = os.path.join(self.directory, filename)
            file_size = os.path.getsize(filepath)
            if offset < 0 or offset + size > file_size or size < 0:
                self.error_handler(BAD_OFFSET)
            # Abrir el archivo en modo lectura binario "rb"
            # 'r' se abrira el archivo en modo lectura y 'b' se abrira en modo binario
            else:
                with open(filepath, "rb") as f:
                    # Lee el slice del archivo especificado, inicia en offset y lee size bytes
                    f.seek(offset)
                    slice_data = f.read(size)
                    self.error_handler(CODE_OK)
                    self.send(slice_data, "b64encode")
    
# Creo un selector de comandos, que se encargará de llamar a los métodos correspondientes
# cmd es un string que representa el comando a ejecutar
    def cmd_selector(self, input):
        """
        Selecciona el comando a ejecutar segun el string cmd
        """
        # Debo trabajar el input para separar el comando de los argumentos
        try:
            print("Received: %s" % input)
            cmd, *args = input.split(" ")
            print(f"Command: {cmd}")
            if cmd == "quit":
                if len(args) == 0:
                    self.quit()
                else:
                    self.error_handler(INVALID_ARGUMENTS)
            elif cmd == "get_metadata":
                if len(args) == 1:
                    self.get_metadata(args[0])
                else:    
                    self.error_handler(INVALID_ARGUMENTS)
            elif cmd == "get_slice":
                if len(args) == 3:
                    self.get_slice(args[0], int(args[1]), int(args[2]))
                else:
                    self.error_handler(INVALID_ARGUMENTS)
            elif cmd == "get_file_listing":
                if len(args) == 0:
                    self.get_file_listing()
                else:
                    self.error_handler(INVALID_ARGUMENTS)
            else:
                self.error_handler(INVALID_COMMAND)
        except Exception as e:
            print(f"Error in connection handling: {e}")


    def _recv(self):
        """
        Recibe datos y acumula en el buffer interno.

        Para uso privado del servidor.
        """
        try:
            data = self.socket.recv(1024)
            data_byte = data.decode("ascii")
            self.buffer += data_byte

            if len(data_byte) == 0:
                self.quit()
            if len(self.buffer) >= 2**32:
                self.error_handler(BAD_REQUEST)
        except UnicodeError:
            self.error_handler(BAD_REQUEST)
        except ConnectionResetError or BrokenPipeError:
            logging.warning("No se pudo contactar al cliente")
            self.connect = False

    def parser(self):
        """
        Espera datos hasta obtener una línea completa delimitada por el
        terminador del protocolo.

        Devuelve la línea sin el terminador ni espacios en blanco al inicio o final.
        """
        while not EOL in self.buffer and self.connect:
            self._recv()
        if EOL in self.buffer:
            response, self.buffer = self.buffer.split(EOL, 1)
            return response.strip()

    def handle(self):
            """
            Atiende eventos de la conexión hasta que termina.
            """
            line = ""
            while self.connect:
                if NEWLINE in line:
                    self.error_handler(BAD_EOL)
                elif len(line) > 0:
                    self.cmd_selector(line)
                line = self.parser()