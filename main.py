import bottle
import sqlite3
from secrets import token_urlsafe

SECURITY_KEY = token_urlsafe(16)

def dict_factory(cursor, row): #custom row factory
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

CONNECTION = sqlite3.connect("path to databbase")
CONNECTION.row_factory = dict_factory
CURSOR = CONNECTION.cursor()


#CRD functions
def get_data(table, query):
    '''ler no bd'''

    def makegetqueryfilters(querystring:str):
        fields = ""
        values = []
        counter = 1
        filtro = querystring.split('&')
        for f in filtro:
            key = f[:f.find('=')]
            fields = fields+key+" = ? AND " if counter< len(filtro) else fields+key+" = ?;"
            counter += 1 
            value = f[f.find('=')+1:]
            values.append(value)
        return {
            "fields":fields,
            "values":values
        }
    
    def executequery(table:str, filters:dict):
        return CURSOR.execute(f"SELECT * FROM {table} WHERE {filters.get('fields')}", filters.get('values')).fetchall()
    
    def main(table, query):
        query_filters = makegetqueryfilters(query)
        response = executequery(table, query_filters)
        return {"response":response}
    
    return main(table, query)

def post_data(table, data:dict):
    '''inserir no bd'''

    def makepostquery(table, data:dict):
        ''' formata o texto da query '''
        fields_string = ""
        values_string = ""
        values_list = []
        counter = 1
        for key in data:
            fields_string = fields_string+f"{key}," if counter<len(data) else fields_string+f"{key}"
            values_string = values_string+f"?," if counter<len(data) else values_string+f"?"
            values_list.append(data.get(key))
            counter += 1
        return {"query_string":f"INSERT INTO {table}({fields_string}) VALUES ({values_string})", "values":values_list}
    
    def executequery(query):
        try:
            CURSOR.execute(query.get("query_string"), query.get("values"))
            CONNECTION.commit()
        except:
            return False
        return True
    
    def main(table, data):
        query = makepostquery(table, data)
        if executequery(query): return {"response":"success"}
        return {"response":"error"}

    return main(table, data)

def delete_data(table, filters):
    '''deletar no bd'''

    def makequery(querystring:str):
        fields = ""
        values = []
        counter = 1
        filtro = querystring.split('&')
        for f in filtro:
            key = f[:f.find('=')]
            fields = fields+key+" = ? AND " if counter< len(filtro) else fields+key+" = ?;"
            counter += 1 
            value = f[f.find('=')+1:]
            values.append(value)
        return {
            "fields":fields,
            "values":values
        }
    
    def executequery(table:str, filters:dict):
        try:
            CURSOR.execute(f"DELETE FROM {table} WHERE {filters.get('fields')}", filters.get('values'))
            CONNECTION.commit()
        except:
            return False
        return True
    
    def main(table, query):
        query_filters = makequery(query)
        if executequery(table, query_filters): return {"response":"success"}
        return {"response":"error"}
    
    return main(table, filters)
    

#views
#exemplo de requisição:
#www.example.com/SECURITY_KEY/TABELA_NO_BD/campo2=valor2&campo2=valor2
@bottle.get('/<key>/<table>/<query>')
def get_method(key, table, query):
    if key != SECURITY_KEY:
        return {"response":"error", "message":"invalid key"}
    return get_data(table, query)

#exemplo de requisição:
#url= www.example.com/SECURITY_KEY/TABELA_NO_BD
#body= {"key":"value"}
@bottle.post('/<key>/<table>')
def post_method(key, table):
    if key != SECURITY_KEY:
        return {"response":"error", "message":"invalid key"}
    request = bottle.request
    data = request.POST
    for d in data.values():
        collection = (("//","/*","*/","DROP"),("<",">","</"))
        for string in collection[0]:
            d.replace(string,"")
        if "<" and ">" and "</" in d:
            for string in collection[1]:
                d.replace(string,"")
    try:
        response = post_data(table, data)
    except:
        response = {"response":"error"}
    return response

#exemplo de requisição:
#www.example.com/SECURITY_KEY/TABELA_NO_BD/campo2=valor2&campo2=valor2
@bottle.delete('/<key>/<table>/<query>')
def delete_method(key, table, query):
    if key != SECURITY_KEY:
        return {"response":"error", "message":"invalid key"}
    return delete_data(table, query)


print("secret key: "+SECURITY_KEY)

bottle.run(host='localhost', port=8080, debug=True)
