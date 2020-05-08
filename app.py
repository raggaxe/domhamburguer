from flask import Flask, session, Markup, Response
from flask import request, render_template, url_for, redirect, flash, send_file, make_response, jsonify
from flask_mail import Mail, Message
from datetime import datetime
from passlib.hash import sha256_crypt
import warnings
from twilio.rest import Client
from dbconnect import connection
from functools import wraps
from werkzeug.utils import secure_filename
import os
from flask import send_from_directory
import random
import math
import json
from SQL_modulos import InsertSql, UpdateQuerySql, SelectSql, SelectAll
import stripe
from twilio.twiml.messaging_response import MessagingResponse



mes = str(datetime.now().strftime("%b"))
dia = str(datetime.now().strftime("%d"))
hora = str(datetime.now().strftime("%H:%M:%S"))

num_Os = []
user_online = []

UPLOAD_FOLDER = './static/uploads/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}



app = Flask(__name__)

mail_settings = {
    'MAIL_SERVER': 'smtp.gmail.com',
    'MAIL_PORT': 465,
    'MAIL_USE_TLS': False,
    'MAIL_USE_SSL': True,
    'MAIL_USERNAME': os.environ['mail_username'],
    'MAIL_PASSWORD': os.environ['mail_password']

}
app.config.update(mail_settings)
mail = Mail(app)

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
secret_key= os.environ['secret_key']
publishable_key = os.environ['publishable_key']
api_key = os.environ['api_key']



app.config['WTF_CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = secret_key
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

stripe_keys = {
  'secret_key': api_key,
  'publishable_key': publishable_key
}



stripe.api_key = stripe_keys['secret_key']
client = Client(account_sid, auth_token)


############ METODOS APLICADOS ####################


def order(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'order' in session:
            return f(*args, **kwargs)
        else:
            flash("Nao possui nenhum pedido")
            return redirect(url_for('index'))
    return wrap

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Precisa fazer o Login")
            return redirect(url_for('index'))
    return wrap

def admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin' in session:
            return f(*args, **kwargs)
        else:
            flash("RESTRITO PARA ADMIN")
            return redirect(url_for('index'))
    return wrap

@app.context_processor
def utility_processor():
    def mes_atual():
        return mes
    def user_name(id):
        user = SelectSql('usuarios','id_usuarios',id)
        for item in user:
            nome = item[1]
        return nome
    def user_email(id):
        user = SelectSql('usuarios','id_usuarios',id)
        for item in user:
            email = item[3]
        return email
    return dict(mes_atual=mes_atual, user_name=user_name, user_email=user_email)

@app.errorhandler(404)
def pag_not_found(e):
    return render_template("404.html")


############ METODOS APLICADOS ####################
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def check_user_Login(login):
    try:
        c, conn = connection()
        x = c.execute(f"""SELECT * FROM usuarios WHERE LOGIN={login}""")
        if int(x) > 0:
            myresult = c.fetchall()
            return myresult
        if int(x) == 0:
            return False
    except Exception as e:
        print(f' ERROR:       {str(e)}')
        return (str(e))
def check_user_ID(id):
    try:
        c, conn = connection()
        x = c.execute(f"""SELECT * FROM usuarios WHERE id_usuario={id}""")
        if int(x) > 0:
            myresult = c.fetchall()
            return myresult
        if int(x) == 0:
            return False
    except Exception as e:
        print(f' ERROR:       {str(e)}')
        return (str(e))
def generateOTP():
    string = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    OTP = ""
    length = len(string)
    for i in range(4):
        OTP += string[math.floor(random.random() * length)]
    return OTP
def generate_invoice():
    string = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    OTP = ''
    length = len(string)
    for i in range(6):
        OTP += string[math.floor(random.random() * length)]
    newOTP=checkInvoice(OTP)
    return newOTP
def checkInvoice(OTP):
    nr = SelectSql('invoice', 'NR_ORDER', OTP)
    if nr == False:
        print('Nao existe')
        return OTP
    else:
        print('newOTP')
        return generate_invoice()
def ADD_pontos(pontos, id):
    user = SelectSql('usuarios', 'id_usuarios', id)
    for x in user:
        add = int(x[6]) + int(pontos)
        UpdateQuerySql({'PONTOS': add}, 'usuarios', 'id_usuarios', id)
############ INDEX ####################
@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        hamburguers = SelectSql('produtos','CATEGORIA','1')
        salgados = SelectSql('produtos','CATEGORIA','2')
        pizzas = SelectSql('produtos', 'CATEGORIA', '3')
        carnes = SelectSql('produtos', 'CATEGORIA', '4')
        bebidas = SelectSql('produtos', 'CATEGORIA', '5')
        print(carnes)
        return render_template('index.html',
                               hamburguers=hamburguers,
                               salgados=salgados,
                               pizzas=pizzas,
                               carnes=carnes,
                               bebidas=bebidas)
    except Exception as e:
        print(f' ERROR:       {str(e)}')
        return (str(e))
# ############ ROTAS DIRETAS ####################
@app.route('/login/', methods=['GET', 'POST'])
def login():
    error = ''
    try:
        if request.method == 'POST':
            email = request.form['EMAIL']
            password = request.form['PASSWORD']
            check_user = SelectSql('usuarios', 'LOGIN', email)

            if check_user == False:
                flash("Login ou Senha Errada, confira e tente novamente", 'erro')
                return redirect(url_for('index'))
            else:
                for person in check_user:
                    id = person[0]
                    check_password = person[4]
                    nome = person[1]
                    end = person[7]
                    ADMIN = person[14]
                    print(ADMIN)
                    if ADMIN == 'True':
                        session['logged_in'] = True
                        session['Nome'] = f'{nome}'
                        session['email'] = email
                        session['ID_User'] = id
                        session['admin'] = True
                        return redirect(url_for('dashboard'))
                    else:
                        if sha256_crypt.verify(password, check_password):
                            session['logged_in'] = True
                            session['email'] = email
                            session['Nome'] = f'{nome}'
                            session['ID_User'] = id
                            session['delivery'] = end
                            print('certo')
                            return redirect(url_for('index'))
                        else:
                            print('senha erro')
                            flash("Login ou Senha Errada, confira e tenta novamente", 'erro')
                            return redirect(url_for('index'))
        return render_template("index.html", error=error)
    except Exception as e:
        # flash(e)
        return redirect(url_for('index'))
@app.route('/register', methods=['POST'])
def register():
    try:
        if request.method == 'POST':
            email = request.form['EMAIL']
            nome = request.form['NOME']
            # apelido = request.form['SOBRENOME']
            check_user = SelectSql('usuarios', 'LOGIN', email)
            print(check_user)
            if check_user == False:
                password = sha256_crypt.encrypt((str(request.form['PASSWORD'])))
                # DATA = str(datetime.now().strftime("%b %d,%Y"))
                myDict = {
                    'LOGIN': email,
                    'PASSWORD': password,
                    'NOME': nome,
                    'ADMIN':'False',
                    'ENDERECO': request.form['ENDERECO'],
                    'TELEFONE': request.form['TELEFONE'],
                    'NOTIFICACOES': 0,
                    'PONTOS': 0,
                    'DATA_INSCRICAO': f'{dia} {mes}',
                    'ENDERECO': False

                }
                InsertSql(myDict, 'usuarios')
                user = SelectSql('usuarios', 'LOGIN', email)
                for item in user:
                    id = item[0]
                session['logged_in'] = True
                session['email'] = email
                session['Completo'] = f'{nome}'
                session['Nome'] = f'{nome}'
                session['ID_User'] = id
                session['delivery'] = False
                return redirect(url_for('index'))
            else:
                flash('Usuário já cadastrado, escolha um email diferente', 'aviso')
                return redirect(url_for('index'))
        return redirect(url_for('index'))

    except Exception as e:
        flash(e)
@app.route('/logout/', methods=['GET', 'POST'])
@login_required
def logout():
    session.clear()
    flash('Voce esta saindo do APP! Obrigado', 'logout')
    return redirect(url_for('index'))


# ############ DASHBOARD ####################
@app.route('/dashboard/', methods=['GET', 'POST'])
@login_required
@admin
def dashboard():
    return render_template('admin/dashboard.html')

@app.route('/dashboard/<function>', methods=['GET', 'POST'])
@login_required
@admin
def function(function):

    if function == 'pedidos':
        orders = []
        listaOrders = []
        pedidos = SelectAll('invoice')
        for i in pedidos:
            if str(i[1]) not in orders:
                te = i[12].split('/')
                t = te[1].split(' -- ')
                mes = t[0]
                data = i[12].split(' -- ')
                orders.append(str(i[1]))
                listaOrders.append([str(i[1]),i[11],i[7],i[8],i[10],mes,i[9],data[0],i[10]])
        # print(listaOrders)

        return render_template('/admin/pedidos.html', orders=listaOrders, order_total = pedidos)
    if function == 'clientes':
        users = SelectAll('usuarios')
        return render_template('/admin/clientes.html', users=users)

    return render_template('/admin/dashboard.html')

# @app.route('/page_forgot_password', methods=['GET', 'POST'])
# def email_forgot():
#     return render_template('redirect.html')


@app.route('/edit/categorias/<categoria>', methods=['GET', 'POST'])
def edit_category(categoria):
    print(categoria)
    produtos = SelectSql('produtos', 'CATEGORIA', categoria)
    if produtos == False:
        produtos = ''
    return render_template('/admin/edit_categoria.html', categoria=categoria, produtos=produtos)

@app.route('/edit/produtos/<id_produto>', methods=['GET', 'POST'])
def edit_produtos(id_produto):
    produto = SelectSql('produtos', 'id_produtos', id_produto)
    return render_template('/admin/edit_produtos.html', produto=produto)

@app.route('/user-Area/<id_data>', methods=['GET', 'POST'])
@login_required
def user_dash_type(id_data):
    print(id_data)
    return redirect(url_for('dashboard'))


    ##### DASHBOARD #####




############ ROTAS LOGIN / DASHBOARD ####################

@app.route('/sms', methods=['GET', 'POST'])
def sms_reply(msg=None):
    comandos = ('/ADD','/REMOVE','/TELEFONES')
    c, conn = connection()
    if msg == None:
            mega = request.form.get('Body')
            message= mega.upper()
            if message in comandos:
                if message == '/ADD':
                    check_in = SelectSql('sms','whatsapp',request.form.get('From') )
                    if check_in == False:
                        InsertSql({'whatsapp': request.form.get('From')},'sms')
                        bg = '✅✅✅ *NUMERO ADICIONADO* ✅✅✅'
                    else:
                        bg = '⚠️⚠️⚠️* NUMERO JÁ CADASTRADO *⚠️⚠️⚠️'
                    client.messages.create(
                        from_='whatsapp:+14155238886',
                        body= bg,
                        to=request.form.get('From')
                    )
                    return str('ok')
                if message == '/REMOVE':
                   c.execute(f"""
                   DELETE FROM sms WHERE whatsapp='{request.form.get('From')}';""")
                   client.messages.create(
                       from_='whatsapp:+14155238886',
                       body='🚨🚨🚨 *NUMERO REMOVIDO* 🚨🚨🚨',
                       to=request.form.get('From')
                   )
                   conn.commit()
                   c.close()
                   return str('ok')


                    # InsertSql({'whatsapp': request.form.get('From')}, 'sms')
                if message == '/TELEFONES':
                    listaTelefones = ''
                    phones = SelectAll('sms')
                    # print(phones)

                    if phones==False:
                       listaTelefones += f'*NENHUM TELEFONE ESTÁ CADASTRADO*\n _para cadastrar digite */ADD*_'

                    else:

                        # numbersToSend = x.fetchall()
                        # print(numbersToSend)
                        for numbersToSend in phones:
                           telefone = numbersToSend[1]
                           print(telefone)
                           listaTelefones += f'*{telefone}*\n'


                    client.messages.create(
                                from_='whatsapp:+14155238886',
                                body=listaTelefones,
                                to=request.form.get('From')
                            )
                    return str('ok')
                if message == '/USUARIOS':
                    listaUsuarios = ''
                    usuarios = SelectAll('usuarios')
                    # print(phones)

                    if usuarios == False:
                        listaUsuarios += f'*NENHUM CLIENTE ESTÁ CADASTRADO*\n _para cadastrar digite */ADD*_'

                    else:
                        # numbersToSend = x.fetchall()
                        # print(numbersToSend)
                        for user in usuarios:
                            # telefone = numbersToSend[1]
                            # print(telefone)
                            listaUsuarios += f'*{user[0]}. - {user[1]}*\n'

                    client.messages.create(
                        from_='whatsapp:+14155238886',
                        body=listaUsuarios,
                        to=request.form.get('From')
                    )
                    return str('ok')


            if message not in comandos:
                resp = MessagingResponse()
                resp.message(f"""
_*🍔DOM HAMBURGUER BOT🍔*_:
Comandos para uso do Sistema:
_________________________________
📞```ADICIONAR SEU NUMERO``` --> */ADD*
📔```WHATSAPP`S CADASTRADOS``` --> */TELEFONES*
⛔```REMOVER SEU NUMERO```- */REMOVER*
________________________________
                """)
                return str(resp)

    else:
        print('ENVIAR PARA OS NUMEROS CADASTRADOS')
        c.execute("SELECT  * FROM sms")
        numbersToSend = c.fetchall()
        for nr in numbersToSend:
            print(nr)
            client.messages.create(
                from_='whatsapp:+14155238886',
                    body=msg,
                    to=nr[1]
                )
        c.close()
@app.route('/transfer/<filename>', methods=['GET', 'POST'])
def uploaded_file(filename):
    if filename == None:
        filename = 'teste'
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)
@app.route('/checkout',methods=['GET', 'POST'])
def checkout():

    user_id = session['ID_User']

    if request.method == 'POST':
        loaded_json = json.loads(request.data)
        print(loaded_json)
        order = generate_invoice()
        session['invoice'] = True
        session['order'] = order


        for myDict in loaded_json:
            myDict.update({'NR_ORDER': order})
            myDict.update({'STATUS': 'invoice'})
            if 'amount' in myDict:
                session['amount'] = myDict['amount']

                # print(session['amount'])
            else:
                # amount = (session['amount'])
                # print(amount)
                myDict.update({'pay_type': 'Null',
                               'AMOUNT': 'Null',
                               'id_user':user_id,
                               'cliente':session['Nome'],
                               'data': f'{dia}/{mes} -- {hora}'})
                InsertSql(myDict, 'invoice')

        msg = ""
        category = "success"
        data_jason = {'msg': msg, 'category': category}

        return make_response(jsonify(data_jason), 200)
    if request.method == 'GET':
        if session['invoice'] == True:
            order = session['order']
            print(order)
            money = '{:,.2f}€'.format(session['amount'] * 0.01)
            pedido = SelectSql('invoice','NR_ORDER',order)
            if pedido == False:
                session.pop('order')
                session.pop('amount')
                session['invoice'] = False
                return redirect(url_for('index'))
            else:
                return render_template('checkout.html', key=stripe_keys['publishable_key'],amount=money,pedido=pedido)
        if session['invoice'] == False:
            return redirect(url_for('index'))
@app.route('/charge', methods=['GET','POST'])
@login_required
@order
def charge():
    whatsappMsg = f"""
❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌
⏰ _DATA: *{dia}/{mes}  --- 🕘 {hora}*
🏓 PEDIDO Nr.: *{session['order']}* \n_
"""
    money = '{:,.2f}€'.format(session['amount'] * 0.01)
    change_status = SelectSql('invoice','NR_ORDER', session['order'])
    for i in change_status:
        whatsappMsg += f""" 🍔: {i[3]}     ----   QNT: {i[5]} \n"""
    if request.method == 'POST':
        print('cartao')
        sms_reply(f""" 
{whatsappMsg} 
_________________________________________
💲💲💲  TOTAL: {money}  💲💲💲
💳💳💳 PAGAMENTO: CARTÃO DE CRÉDITO 💳💳💳
❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌""")
        for all in change_status:
            myDict = {'STATUS': 'OK','pay_type': 'card','AMOUNT': money}
            UpdateQuerySql(myDict, 'invoice','NR_ORDER', session['order'])



        customer = stripe.Customer.create(
            email=session['email'],
            source=request.form['stripeToken']
        )

        stripe.Charge.create(
            customer=customer.id,
            amount = session['amount'],
            currency='eur',
            description=session['Nome']
        )

        session.pop('order')
        session.pop('amount')
        session['invoice'] = False

        return render_template('charge.html')

    if request.method == 'GET':
        sms_reply(f""" 
{whatsappMsg} 
_________________________________________
💲💲💲  TOTAL: {money}  💲💲💲
💶💶💶 PAGAMENTO: DINHEIRO NA ENTREGA 💶💶💶
❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌""")
        for all in change_status:
            myDict = {'STATUS': 'OK', 'pay_type': 'dinheiro', 'AMOUNT': money}
            UpdateQuerySql(myDict, 'invoice', 'NR_ORDER', session['order'])

        session.pop('order')
        session.pop('amount')
        session['invoice'] = False
        return render_template('charge.html')

@app.route('/edit_produto', methods=['GET', 'POST'])
def edit_produto():
    if request.method == "POST":
        try:
            data = []
            myDict = {}
            for post in request.form:
                if 'ingredientes_' in post:
                    data.append(post)

            recipe = ''
            recipe_lista = []
            for form in data:
                request_form = request.form[form]
                recipe_lista.append(request_form)
                recipe += f'{request_form}; '

            count = len(recipe_lista)
            print(count)

            myDict.update({
                'PRODUTO': request.form['titulo'],
                'VALOR': request.form['valor'],
                'INGREDIENTES': recipe,
                'VALOR_INGREDIENTES': count,
                'TIME': request.form['time'],
                'SERVING': request.form['serving_edit'],
                'CATEGORIA': request.form['categoria']
            })

            if request.files.getlist('files'):
                for file in request.files.getlist('files'):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    myDict.update({'FOTO': filename})
            else:
                pass



            if SelectSql('produtos', 'id_produtos', request.form['id']) != False:

                msg = "OK, PRODUTO EDITADO COM SUCESSO."
                category = "success"
                data_jason = {'msg': msg, 'category': category}

                 # InsertSql(myDict, 'produtos')
                UpdateQuerySql(myDict, 'produtos','id_produtos', request.form['id'])
                # return make_response(jsonify(data_jason), 200)
                # return redirect(url_for('edit_category', categoria='1'))

            else:
                msg = "PRODUTO NÃO EXISTENTE."
                category = "danger"
                data_jason = {'msg': msg, 'category': category}
                # return make_response(jsonify(data_jason), 200)


        except Exception as err:
            msg = "ALGO ERRADO ! PREENCHA TODO O FORMULÁRIO."
            category = "danger"
            data_jason = {'msg': msg, 'category': category}
            # return make_response(jsonify(data_jason), 200)

    return make_response(jsonify(data_jason), 200)
    # return redirect(url_for('edit_category', categoria='1'))

@app.route('/insert_produto', methods=['GET', 'POST'])
def insert_produto():
    if request.method == "POST":
        try:

            data = []
            myDict = {}
            for post in request.form:
                if 'ingredientes_' in post:
                    data.append(post)

            recipe = ''
            recipe_lista = []
            for form in data:
                request_form = request.form[form]
                recipe_lista.append(request_form)
                recipe += f'{request_form}; '
            count = len(recipe_lista)


            myDict.update({
                'PRODUTO': request.form['titulo'],
                'VALOR': request.form['valor'],
                'INGREDIENTES': recipe,
                'VALOR_INGREDIENTES': count,
                'TIME': request.form['time'],
                'SERVING': request.form['serving'],
                'CATEGORIA': request.form['categoria']
            })
            if request.files.getlist('files'):
                for file in request.files.getlist('files'):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    myDict.update({'FOTO': filename})
            else:
                myDict.update({'FOTO': 'box_hamburger.jpg'})

            # UpdateQuerySql(myDict, 'usuarios','EMAIL',session['email'])
            # print(myDict)
            if SelectSql('produtos', 'PRODUTO', request.form['titulo']) == False:

                msg = "OK, PRODUTO INSERIDO COM SUCESSO! CONFIRA COMO FICARÁ SEU ANUNCIO."
                category = "success"
                data_jason = {'msg': msg, 'category': category}

                InsertSql(myDict, 'produtos')
                # return make_response(jsonify(data_jason), 200)
            else:
                msg = "PRODUTO JA CADASTRADO."
                category = "danger"
                data_jason = {'msg': msg, 'category': category}
                # return make_response(jsonify(data_jason), 200)


        except Exception as err:
            msg = "ALGO ERRADO ! PREENCHA TODO O FORMULÁRIO."
            category = "danger"
            data_jason = {'msg': msg, 'category': category}
            # return make_response(jsonify(data_jason), 200)

    return make_response(jsonify(data_jason), 200)



############ ROTAS DE TRABALHO ####################


#
#         ##### EMAIL FORGOT / TOKEN  #####
#
#
#
# @app.route('/token/<string:email>', methods=['GET', 'POST'])
# def token(email):
#     token = generateOTP()
#     print(token)
#     UpdateQuerySql({'OTP': token}, 'usuarios', 'EMAIL', email)
#     user = SelectSql('usuarios', 'LOGIN', email)
#     for item in user:
#         # id = item[0]
#         nome_completo = f'{item[3]} {item[4]}'
#     if __name__ == '__main__':
#         with app.app_context():
#             msg = Message(subject='Pedido de Nova Senha',
#                           sender=app.config.get('MAIL_USERNAME'),
#                           recipients=[email],
#                           html=render_template('email_reply.html', token=token, user=nome_completo))
#             mail.send(msg)
#             flash('Verifique o seu e-mail, um novo código foi enviado.', 'login')
#             return render_template('insert_code.html', email=email)
#
# @app.route('/send_email_password', methods=['GET', 'POST'])
# def index_mail():
#     email = request.form['email']
#     token = generateOTP()
#     print(token)
#     user = SelectSql('usuarios','LOGIN',email)
#     if user == False:
#         flash(f'Esse email não está cadastrado!!! Verifique se está correto o email {email}','erro')
#         return redirect(url_for('email_forgot'))
#     else:
#         UpdateQuerySql({'OTP': token}, 'usuarios', 'EMAIL',email)
#         for item in user:
#             nome_completo = f'{item[3]} {item[4]}'
#         if __name__ == '__main__':
#             with app.app_context():
#                 msg = Message(subject='Código para alteração de password Guia Figueira da Foz',
#                             sender=app.config.get('MAIL_USERNAME'),
#                               recipients=[email],
#                               html=render_template('email_reply.html',token=token, user=nome_completo))
#                 mail.send(msg)
#                 return render_template('insert_code.html', email=email)
#
#
# @app.route('/confima_code', methods=['GET', 'POST'])
# def confirma_code():
#     if request.method == "POST":
#         email = request.form['email']
#         code = request.form['code']
#         new_password = sha256_crypt.encrypt((str(request.form['new_password'])))
#         data = SelectSql('usuarios', 'LOGIN',email)
#         for item in data:
#             OTP = item[12]
#             if str(OTP) == str(code):
#                 UpdateQuerySql({'PASSWORD':new_password}, 'usuarios','EMAIL',email)
#                 flash('Senha Atualizada com Sucesso!', 'success')
#                 return redirect(url_for('LoginClientes'))
#             else:
#                 flash('Código não está correto, tente novamente', 'erro')
#                 return render_template('insert_code.html',email=email)
#
#
#
#         ####### REGISTER USUARIOS ##########

#






# ############## CONFIGURACOES DE USUARIOS #################
#
# @app.route('/edit_profile_photo', methods=['GET', 'POST'])
# def edit_profile_photo():
#     if request.method == "POST":
#         myDict = {}
#         if request.files['file']:
#             f = request.files['file']
#             print(f)
#             if f and allowed_file(f.filename):
#                 filename = secure_filename(f.filename)
#                 f.save(os.path.join(app.config['UPLOAD_FOLDER'], 'avatar'+filename))
#                 myDict.update({'FOTO':'avatar'+filename})
#         UpdateQuerySql(myDict, 'usuarios','EMAIL',session['email'])
#         return redirect(url_for('dashboard'))
#
#
# @app.route('/usuarios/', methods=['GET', 'POST'])
# def usuarios():
#     c, conn = connection()
#     c.execute("SELECT  * FROM usuarios")
#     data = c.fetchall()
#     c.close()
#     return render_template('lista-Usuarios.html', usuarios=data )
#
#
#
# @app.route('/edit_usuario', methods=['GET', 'POST'])
# def edit_usuario():
#     if request.method == "POST":
#         data = []
#         myDict = {}
#         for post in request.form:
#             data.append(post)
#         for form in data:
#             request_form = request.form[form]
#             print(request_form)
#             myDict.update({form: request_form})
#             if request_form == '':
#                 request_form = "blank"
#                 myDict.update({form: request_form})
#             else:
#                 myDict.update({form: request_form})
#         print(myDict)
#         UpdateQuerySql(myDict, 'usuarios', 'EMAIL', session['email'])
#     return redirect(url_for('dashboard'))
#
#
# @app.route('/delete/<string:id_data>', methods = ['GET'])
# def delete(id_data):
#     flash("Record Has Been Deleted Successfully")
#     c, conn = connection()
#     c.execute("DELETE FROM usuarios WHERE id_usuario=%s", (id_data,))
#     return redirect(url_for('usuarios'))
#
#


def main():
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True)
if __name__ == "__main__":
    main()
