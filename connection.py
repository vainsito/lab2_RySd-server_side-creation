# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import socket
from constants import *
from base64 import b64encode

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

    def quit(self):
        """
        Termina la conexión con el cliente.
        """
        status = CODE_OK
        self.socket.send(b"Bye!\n")
        self.socket.close()
        
    def get_file_listing(self):
        """
        Devuelve una lista de los archivos en el directorio del servidor.
        """
        return 
    
    def get_metadata(self, filename):
        """
        Devuelve un diccionario con los metadatos del archivo filename.
        """
        return
    
    def get_slice(self, filename, offset, size):
        """
        Devuelve una parte del archivo filename, comenzando en offset y
        con un tamaño de size bytes.
        """
        return
    
    
# Creo un selector de comandos, que se encargará de llamar a los métodos correspondientes
# cmd es un string que representa el comando a ejecutar
    def cmd_selector(self, cmd):
        """
        Selecciona el comando a ejecutar segun el string cmd
        """
        if cmd == "quit":
            self.quit()
        elif cmd == "get":
            self.get()
        elif cmd == "quit":
            self.quit()
        else:
            self.unknown()

    def handle(self):
        """
        Atiende eventos de la conexión hasta que termina.
        """
        # FALTA: Loop principal de la conexión\