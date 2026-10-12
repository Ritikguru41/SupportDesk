"""
Config package initialization.
Ensures PyMySQL acts as MySQLdb for Django MySQL database backend.
"""
import pymysql

pymysql.install_as_MySQLdb()
