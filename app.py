from flask import Flask, render_template, request, abort, json
from pymongo import MongoClient
import pandas as pd
#import matplotlib.pyplot as plt
import os
import unicodedata

# Para este ejemplo pediremos la id
# y no la generaremos automáticamente
USER_KEYS = ['uid', 'name',
            'age', 'description']

#No incluyo el mid puesto que se lo debo asignar yo
messages_keys = ["date", "lat", "long", "message", "receptant", "sender"]

USER = "grupo64"
PASS = "grupo64"
DATABASE = "grupo64"

# El cliente se levanta en la URL de la wiki
# URL = "mongodb://grupoXX:grupoXX@gray.ing.puc.cl/grupoXX"
URL = f"mongodb://{USER}:{PASS}@gray.ing.puc.cl/{DATABASE}"
client = MongoClient(URL)

# Utilizamos la base de datos del grupo
db = client["grupo64"]

# Seleccionamos la collección de usuarios
usuarios = db.usuarios
mensajes=db.mensajes



def strip_accents(text):

    try:
        text = unicode(text, 'utf-8')
    except NameError: # unicode is a default on python 3 
        pass

    text = unicodedata.normalize('NFD', text)\
           .encode('ascii', 'ignore')\
           .decode("utf-8")

    return str(text)





'''
Usuarios:
  "uid": <id del usuario>,
  "name": <nombre>,
  "last_name": <apellido>,
  "age": <edad>,
  "occupation": <a qué se dedica>,
  "follows": [<arreglo con una lista de ids de usuarios>]
'''

# Iniciamos la aplicación de flask
app = Flask(__name__)

@app.route("/")
def home():
    '''
    Página de inicio
    '''
    return "<h1>¡Hola, subi algo nuevo! 2</h1>"

# Mapeamos esta función a la ruta '/plot' con el método get.
@app.route("/plot")
def plot():
    '''
    Muestra un gráfico a partir de los datos ingresados
    '''
    # Ejemplo no directamente relacionado con la entrega
    # Pero que muestra las cosas que son posibles hacer
    # con nuestra API

    # Obtenermos todos los usuarios
    users = usuarios.find({}, {"_id": 0})

    # Hacemos un data frame (tabla poderosa) con la columna
    # 'name' indexada
    df = pd.DataFrame(list(users)).set_index('name')

    # Hacemos un gráfico de pi en base a la edad
    df.plot.pie(y='age')

    # Export la figura para usarla en el html
    pth = os.path.join('static', 'plot.png')
    plt.savefig(pth)

    # Retorna un html "rendereado"
    return render_template('plot.html')

@app.route("/users")
def get_users():
    '''
    Obtiene todos los usuarios
    '''
    # Omitir el _id porque no es json serializable
    resultados = list(usuarios.find({}, {"_id": 0}))
    return json.jsonify(resultados)

@app.route("/messages")
def get_messages():
    '''
    Obtiene todos los mensajes
    '''
    # Omitir el _id porque no es json serializable

    param1 = int(request.args.get('id1', False))
    param2 = int(request.args.get('id2', False))

    if (param1 == 0) and (param2 == 0):
        resultados = list(mensajes.find({}, {"_id": 0}))
        return json.jsonify(resultados)

    else:

        resultado_intercambio = list(mensajes.find( { "$or":[ { "$and":[{"sender":param1},{"receptant":param2}] } , { "$and":[{"sender":param2},{"receptant":param1}] } ] } , {"_id":0} ) )
        
        if resultado_intercambio == []:
            return json.jsonify({"error": "no hay mensajes existentes entre los dos usuarios"})


        return json.jsonify(resultado_intercambio)




@app.route("/messages/<int:mid>")
def get_message(mid):
    '''
    Obtiene el mensaje de mid entregada
    '''
    mensajes_a_mostrar = list(mensajes.find({"mid": mid}, {"_id": 0}))

    if mensajes_a_mostrar == []:
        return json.jsonify({"error": f"no existe el id = {mid}"})


    return json.jsonify(mensajes_a_mostrar)


###ENTREGA 5

@app.route("/enviados/<int:sender>")
def get_message_enviados(sender):
    '''
    Obtiene todos los atributos de los mensajes recibidos por el usuario connectado
    '''
    mensajes_a_mostrar = list(mensajes.find({"sender": sender}, {"_id": 0}))

    if mensajes_a_mostrar == []:
        return json.jsonify({"error": f"no existe mensajes enviados por id = {sender}"})


    return json.jsonify(mensajes_a_mostrar)

@app.route("/recividos/<int:receptant>")
def get_message_recividos(receptant):
    '''
    Obtiene todos los atributos de los mensajes recibidos por el usuario connectado
    '''
    mensajes_a_mostrar = list(mensajes.find({"receptant": receptant}, {"_id": 0}))

    if mensajes_a_mostrar == []:
        return json.jsonify({"error": f"no existe mensajes recividos por id = {receptant}"})


    return json.jsonify(mensajes_a_mostrar)


@app.route("/users/<int:uid>")
def get_user(uid):
    '''
    Obtiene el usuario de id entregada
    '''
    users = list(usuarios.find({"uid": uid}, {"_id": 0}))
    users_mensajes = list(mensajes.find({"sender":uid},{"message":1,"_id": 0}))
    final = users + users_mensajes

    if final == []:
        return json.jsonify({"error": f"no existe el id = {uid}"})

    return json.jsonify(final)

@app.route("/users/username/<string:name>")
def get_username(name):
    '''
    Obtiene el usuario de id entregada
    '''
    users = list(usuarios.find({"name": name}, {"_id": 0}))

    if users == []:
        return json.jsonify({"error": f"no existe el username {name}"})

    return json.jsonify(users)


@app.route("/users", methods=['POST'])
def create_user():
    '''
    Crea un nuevo usuario en la base de datos
    Se  necesitan todos los atributos de model, a excepcion de _id
    '''

    # En este caso nos entregarán la id del usuario,
    # Y los datos serán ingresados como json
    # Body > raw > JSON en Postman
    data = {key: request.json[key] for key in USER_KEYS}

    # El valor de result nos puede ayudar a revisar
    # si el usuario fue insertado con éxito
    result = usuarios.insert_one(data)

    return json.jsonify({'success': True, 'message': 'Usuario con id 1 creado'})




@app.route("/text-search")
def textsearch():

    text_search_keys = ["desired", "required", "forbidden", "userId"]
    contador = 0
    data = {}
    data_mala = {}

    #all_data = request.json
    #all_data = request.data
    all_data = access_token = request.data.decode('UTF-8')

    if all_data == "":
        resultados = list(mensajes.find({}, {"_id": 0}))
        return json.jsonify(resultados)

    all_data = request.json

    
    if isinstance(all_data, dict) == False:
        resultados = list(mensajes.find({}, {"_id": 0}))
        return json.jsonify(resultados)

    if all_data == {}:
        resultados = list(mensajes.find({}, {"_id": 0}))
        return json.jsonify(resultados)

    if len(all_data)==1:

        if "desired" in all_data.keys():
            palabras = all_data["desired"]

            if palabras == []:
                resultados = list(mensajes.find({}, {"_id": 0}))
                return json.jsonify(resultados)
            else:
                palabra_final= ""
                for palabra in palabras:
                    palabra_final = palabra_final + " " + palabra
                variable_a_retornar = list(mensajes.find({"$text": {"$search": palabra_final} },{"score": {"$meta": "textScore"}, "mid":1, "message": 1,"sender":1 , "_id": 0}).sort([ ("score", {"$meta": "textScore"}) ]))
                return json.jsonify(variable_a_retornar)


        if "required" in all_data.keys():
            palabras = all_data["required"]

            if palabras == []:
                resultados = list(mensajes.find({}, {"_id": 0}))
                return json.jsonify(resultados)
            else:
                palabra_final= ""
                for palabra in palabras:
                    palabra_final = palabra_final + """\"""" + palabra + """\" """
                variable_a_retornar = list(mensajes.find({"$text": {"$search": palabra_final} },{"score": {"$meta": "textScore"}, "mid":1, "message": 1,"sender":1 , "_id": 0}).sort([ ("score", {"$meta": "textScore"}) ]))
                return json.jsonify(variable_a_retornar)

        if "forbidden" in all_data.keys():
            palabras = all_data["forbidden"] #["hola, "chao]
   
            if palabras == []:
                resultados = list(mensajes.find({}, {"_id": 0}))
                return json.jsonify(resultados)

            else:
                resultados = list(mensajes.find({}, {"_id": 0}))
                lista_mensajes = []
                lista_strings_a_borrar = []

                for resultado in resultados:

                    resultado_limpio = strip_accents(resultado["message"].lower())
                    mensaje_id = resultado["mid"]

                    lista_mensajes.append([resultado_limpio, mensaje_id])

                for resultado in resultados:

                    resultado_limpio = strip_accents(resultado["message"].lower())

                    for palabra in palabras:

                        palabra_limpia = strip_accents(palabra.lower())

                        if palabra_limpia in resultado_limpio:

                            lista_strings_a_borrar.append(resultado_limpio)
                            break

                for mensaje_borrar in lista_strings_a_borrar:

                    for lista_real in lista_mensajes:

                        if lista_real[0] == mensaje_borrar:

                            lista_mensajes.remove(lista_real)
                            break


            return json.jsonify(lista_mensajes)





        if "userId" in all_data.keys():

            user = all_data["userId"]
            resultados = list(mensajes.find({"sender":user }, {"_id": 0}))
            return json.jsonify(resultados)


    else:
        for key in text_search_keys:

            if contador == 0:

                lista_palabras_deseadas = request.json[key]
                boleano = isinstance(lista_palabras_deseadas, list)  #vemos si es una lista

                if boleano == True:
                    boleano_default = True
                    for palabra in lista_palabras_deseadas:
                        if (isinstance(palabra, str)) == True:
                            boleano_default = True
                        else:
                            boleano_default = False
                            data_mala[key] = lista_palabras_deseadas
                            return json.jsonify({'desired': data_mala["desired"], 'error': "Debes introducir elementos de tipo string"})

                    data[key] = lista_palabras_deseadas
                    data_mala[key] = lista_palabras_deseadas

                else:
                    data_mala[key] = lista_palabras_deseadas
                    return json.jsonify({'desired': data_mala["desired"], 'error': "Debes introducir una lista en desired"})

            elif contador == 1:

                lista_palabras_requeridas = request.json[key]
                boleano = isinstance(lista_palabras_requeridas, list)  #vemos si es una lista

                if boleano == True:
                    boleano_default = True
                    for palabra in lista_palabras_requeridas:
                        if (isinstance(palabra, str)) == True:
                            boleano_default = True
                        else:
                            boleano_default = False
                            data_mala[key] = lista_palabras_requeridas
                            return json.jsonify({'desired': data_mala["desired"], 'required': data_mala["required"], 'error': "Debes introducir elementos de tipo string"})

                    data[key] = lista_palabras_requeridas
                    data_mala[key] = lista_palabras_requeridas

                else:
                    data_mala[key] = lista_palabras_requeridas
                    return json.jsonify({'desired': data_mala["desired"], 'required': data_mala["required"],'error': "Debes introducir una lista en required"})

            elif contador == 2:

                lista_palabras_prohibidas = request.json[key]
                boleano = isinstance(lista_palabras_prohibidas, list)  #vemos si es una lista

                if boleano == True:
                    boleano_default = True
                    for palabra in lista_palabras_prohibidas:
                        if (isinstance(palabra, str)) == True:
                            boleano_default = True
                        else:
                            boleano_default = False
                            data_mala[key] = lista_palabras_prohibidas
                            return json.jsonify({'desired': data_mala["desired"], 'required': data_mala["required"], 'forbidden': data_mala["forbidden"], 'error': "Debes introducir elementos de tipo string"})

                    data[key] = lista_palabras_prohibidas
                    data_mala[key] = lista_palabras_prohibidas

                else:
                    data_mala[key] = lista_palabras_prohibidas
                    return json.jsonify({'desired': data_mala["desired"], 'required': data_mala["required"], 'forbidden': data_mala["forbidden"], 'error': "Debes introducir una lista en forbidden"})

            elif contador == 3:

                sender_id = request.json[key]
                boleano = isinstance(sender_id, int)  #vemos si sender es un int

                if (boleano == True):

                    lista_de_todos_los_usuarios = usuarios.find({}, {"uid":1 , "_id":0})
                    lista_con_todos_los_uid = []

                    for diccionario in lista_de_todos_los_usuarios:
                        lista_con_todos_los_uid.append(diccionario["uid"])

                    if (sender_id in lista_con_todos_los_uid) == True:
                        data[key] = sender_id
                        data_mala[key] = sender_id

                    else:
                        data_mala[key] = sender_id
                        return json.jsonify({'desired': data_mala["desired"], 'required': data_mala["required"], 'forbidden': data_mala["forbidden"], 'userId': data_mala["userId"], 'error': "Debes introducir un userid que este en la base de datos"})

                else:
                    data_mala[key] = sender_id
                    return json.jsonify({'desired': data_mala["desired"], 'required': data_mala["required"], 'forbidden': data_mala["forbidden"], 'userId': data_mala["userId"], 'error': "Debes introducir un userid que sea un int"})

            contador = contador + 1


        palabra_final = """ """
        palabras_requeridas_lista = data["required"]
        for palabra in palabras_requeridas_lista:
            palabra_final = palabra_final + """\"""" + palabra + """\" """

        palabras_deseadas_lista = data["desired"]
        for palabra in palabras_deseadas_lista:
            palabra_final = palabra_final + " " + palabra

        palabra_final = palabra_final + " "

        palabras_prohibidas_lista = data["forbidden"]

        for palabra in palabras_prohibidas_lista:
            palabra_final = palabra_final + "-" + palabra + " "


        print(palabra_final)


        varibale_a_retornar = list(mensajes.find({"sender":data["userId"], "$text": {"$search": palabra_final} },{"score": {"$meta": "textScore"}, "mid":1, "message": 1,"sender":1 , "_id": 0}).sort([ ("score", {"$meta": "textScore"}) ]))

        return json.jsonify(varibale_a_retornar)



#CREA MENSAJE CON EL METODO POST
@app.route("/messages", methods=['POST'])
def create_a_message():
    #messages_keys = ["date", "lat", "long", "message", "receptant", "sender"]
    #data = {key: request.json[key] for key in USER_KEYS}

    all_data = request.json
    print(all_data)

    for key in messages_keys:

        if (key in all_data) == False:
            return json.jsonify({"error" : f"falta el atributo {key}"})
        else:
            pass



    data = {}
    data_mala = {}
    contador = 0
    for key in messages_keys:

        if contador == 0:

            fecha = request.json[key]
            boleano = isinstance(fecha, str)  #vemos si fecha es un string

            if boleano == True:
                data[key] = fecha
                data_mala[key] = fecha

            else:
                data_mala[key] = fecha
                return json.jsonify({'date': data_mala["date"], 'error': "Debes introducir una fecha que sea un string"})

        elif contador == 1:

            lat = request.json[key]
            boleano_1 = isinstance(lat, int)  #vemos si lat es un int
            boleano_2 = isinstance(lat, float)  #vemos si lat es un float

            if (boleano_1 == True or boleano_2 == True):

                data[key] = lat
                data_mala[key] = lat

            else:
                data_mala[key] = lat
                return json.jsonify({'date': data_mala["date"], 'lat': data_mala["lat"], 'error': "Debes introducir una lat que sea un int o un float"})

        elif contador == 2:

            variable_long = request.json[key]
            boleano_1 = isinstance(variable_long, int)  #vemos si lat es un int
            boleano_2 = isinstance(variable_long, float)  #vemos si lat es un float

            if (boleano_1 == True or boleano_2 == True):

                data[key] = variable_long
                data_mala[key] = variable_long

            else:
                data_mala[key] = variable_long
                return json.jsonify({'date': data_mala["date"], 'lat': data_mala["lat"], 'long': data_mala["long"], 'error': "Debes introducir un long que sea un int o un float"})


        elif contador == 3:

            mensaje_recibido = request.json[key]
            boleano = isinstance(mensaje_recibido, str)  #vemos si mensaje es un string

            if boleano == True:
                data[key] = mensaje_recibido
                data_mala[key] = mensaje_recibido

            else:
                data_mala[key] = mensaje_recibido
                return json.jsonify({'date': data_mala["date"], 'lat': data_mala["lat"], 'long': data_mala["long"], 'message': data_mala["message"], 'error': "Debes introducir un mensaje que sea un string"})

        elif contador == 4:

            receptant = request.json[key]
            boleano = isinstance(receptant, int)  #vemos si receptant es un int

            if (boleano == True):

                lista_de_todos_los_usuarios = usuarios.find({}, {"uid":1 , "_id":0})
                lista_con_todos_los_uid = []

                for diccionario in lista_de_todos_los_usuarios:
                    lista_con_todos_los_uid.append(diccionario["uid"])

                if (receptant in lista_con_todos_los_uid) == True:
                    data[key] = receptant
                    data_mala[key] = receptant

                else:
                    data_mala[key] = receptant
                    return json.jsonify({'date': data_mala["date"], 'lat': data_mala["lat"], 'long': data_mala["long"], 'message': data_mala["message"], 'receptant': data_mala["receptant"], 'error': "Debes introducir un receptant que sea parte de los usuarios de la base de datos. Además recuerda que de debe ser del tipo int"})

            else:
                data_mala[key] = receptant
                return json.jsonify({'date': data_mala["date"], 'lat': data_mala["lat"], 'long': data_mala["long"], 'message': data_mala["message"], 'receptant': data_mala["receptant"], 'error': "Debes introducir un receptant que sea un int"})


        elif contador == 5:


            sender = request.json[key]
            boleano = isinstance(sender, int)  #vemos si sender es un int

            if (boleano == True):

                lista_de_todos_los_usuarios = usuarios.find({}, {"uid":1 , "_id":0})
                lista_con_todos_los_uid = []

                for diccionario in lista_de_todos_los_usuarios:
                    lista_con_todos_los_uid.append(diccionario["uid"])

                if (sender in lista_con_todos_los_uid) == True:
                    data[key] = sender
                    data_mala[key] = sender

                else:
                    data_mala[key] = sender
                    return json.jsonify({'date': data_mala["date"], 'lat': data_mala["lat"], 'long': data_mala["long"], 'message': data_mala["message"], 'receptant': data_mala["receptant"], 'sender': data_mala["sender"], 'error': "Debes introducir un sender que sea parte de los usuarios de la base de datos. Además recuerda que de debe ser del tipo int"})

            else:
                data_mala[key] = sender
                return json.jsonify({'date': data_mala["date"], 'lat': data_mala["lat"], 'long': data_mala["long"], 'message': data_mala["message"], 'receptant': data_mala["receptant"], 'sender': data_mala["sender"], 'error': "Debes introducir un sender que sea un int"})

        contador = contador + 1




    lista_de_todos_los_mensajes = list(mensajes.find({}, {"mid": 1 , "_id": 0}))
    lista_con_todos_los_mid = []

    for diccionario in lista_de_todos_los_mensajes:

        lista_con_todos_los_mid.append(diccionario["mid"])

    lista_con_todos_los_mid.sort()   #ordenamos de mayor a menor los mid
    tamano_lista_con_todos_los_mid = len(lista_con_todos_los_mid)
    ultimo_mid = lista_con_todos_los_mid[tamano_lista_con_todos_los_mid - 1]
    mid_a_asignar = ultimo_mid + 1

    data["mid"] = mid_a_asignar

    mensajes.insert_one(data)

    return json.jsonify({'date': data["date"], 'lat': data["lat"], 'long': data["long"], 'message': data["message"], 'receptant': data["receptant"], 'sender': data["sender"], 'mid': data["mid"]})


#DELETE (BORRAR UN MENSAJE DADO EL ID ENTREGADO)
@app.route("/message/<int:mid>", methods=['DELETE'])
def borrar_mensaje(mid):

    lista_de_todos_los_mensajes = list(mensajes.find({}, {"mid": 1 , "_id": 0}))
    lista_con_todos_los_mid = []

    for diccionario in lista_de_todos_los_mensajes:

        lista_con_todos_los_mid.append(diccionario["mid"])

    if (mid in lista_con_todos_los_mid) == True:

        borrar_mensaje = list(mensajes.remove({"mid":mid}, "true"))
        borrar_mensaje.append({"Comentario del backend": f"Se borró exitosamente el mensaje con mid={mid}"})
        return json.jsonify(borrar_mensaje)

    else:

        return json.jsonify({'Comentario del backend': f"No se puedo borrar el mensaje, puesto que no existía el mensaje con mid= {mid} en la base de datos"})



@app.route("/test")
def test():
    # Obtener un parámero de la URL
    # Ingresar desde Params en Postman
    # O agregando ?name=... a URL
    param = request.args.get('name', False)
    print("URL param:", param)

    # Obtener un header
    # Ingresar desde Headers en Postman
    param2 = request.headers.get('name', False)
    print("Header:", param2)

    # Obtener el body
    # Ingresar desde Body en Postman
    body = request.data
    print("Body:", body)

    return f'''
            OK
            <p>parámetro name de la URL: {param}<p>
            <p>header: {param2}</p>
            <p>body: {body}</p>
            '''



if __name__ == "__main__":
    app.run(debug=True)
    # app.run(debug=True) # Para debuggear!
# ¡Mucho ánimo y éxito! ¡Saludos! :D
