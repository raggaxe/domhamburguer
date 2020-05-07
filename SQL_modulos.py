from dbconnect import connection

import warnings

def InsertSql(myDict,table):
    try:
        print('INSERINDO....')
        c, conn = connection()

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            columns = ', '.join("`" + str(x).replace('/', '_') + "`" for x in myDict.keys())
            values = ', '.join("'" + str(x) + "'" for x in myDict.values())

            c.execute('SET @@auto_increment_increment=1;')
            conn.commit()
            sql = "INSERT INTO %s ( %s ) VALUES ( %s );" % (table, columns, values)
            c.execute(sql)
            conn.commit()
        # print(f'INSERIDO : { myDict} {{status :: OK}} ')
    except Exception as e:
        print(f' ERROR:       {str(e)}')
        return (str(e))
def SelectSql(table, coluna,value):
    try:
        c,conn = connection()
        x = c.execute(f"""SELECT * FROM {table} WHERE {coluna}= '{value}'""")
        if int(x) > 0:
            myresult = c.fetchall()
            return myresult
        if int(x) == 0:
            return False
    except Exception as e:
        print(f' ERROR:       {str(e)}')
        return (str(e))

def SelectAll(table):
    try:
        c,conn = connection()
        x = c.execute(f"""SELECT * FROM {table}""")
        if int(x) > 0:
            myresult = c.fetchall()
            return myresult
        if int(x) == 0:
            return False
    except Exception as e:
        print(f' ERROR:       {str(e)}')
        return (str(e))

def UpdateQuerySql(mydict,table,item,modifica):
    print(' ATUALIZANDO DADOS .... ')
    c, conn = connection()
    for k in mydict:
        coluna = (k)
        value = (mydict[k])
        sql = (f"""UPDATE `{table}` SET `{coluna}` = '{value}' WHERE (`{item}` = '{modifica}');""")
        c.execute(sql)
        conn.commit()
        conn.close
    print(f'--->>> ATUALIZAÇÃO da TABELA :{table}  == > DATA {mydict}{{status :: OK}} .... ')



def delete_all_rows(table):
    try:
        print(f'DELETENDO ITENS DA TABELA {table}....')
        c, conn = connection()
        sql = "DELETE FROM %s ;" % (table)
        c.execute(sql)
        conn.commit()
        print('TODAS AS ROWS FORAM DELETADAS {{status :: OK}} ')
    except Exception as e:
        print(f' ERROR:       {str(e)}')
        return (str(e))

