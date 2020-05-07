import pymysql
import os
def connection():
    conn = pymysql.connect(host=os.environ['host'],
                           user=os.environ['user'],
                           passwd=os.environ['passwd'],
                           db = os.environ['db'])
    c = conn.cursor()

    return c,conn
