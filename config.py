# config.py
import cx_Oracle

ORACLE_USERNAME = "DB_221ADB119"
ORACLE_PASSWORD = "CFSQRAQMVE"
ORACLE_DSN = cx_Oracle.makedsn("85.254.224.178", 1521, sid="dblab01")
SECRET_KEY = "119"
