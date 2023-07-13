from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
from config import config
import time
from flask_login import LoginManager,login_user,logout_user,login_required
import csv
from flask import send_file


#Models
from src.ModelUser import ModelUser

#Entities
from src.entities.User import User

app = Flask(__name__)

csrf = CSRFProtect()

#Mysql connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'abcd1234'
app.config['MYSQL_DB'] = 'process'
mysql = MySQL(app)

login_manager_app=LoginManager(app)

@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(mysql,id)

#Settings
app.secret_key='mysecretkey'

@app.route("/")
def index():
    return redirect(url_for('login'))

@app.route("/perfil")
@login_required
def Perfil():
    return render_template("perfil.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method=="POST":
       user = User(0,request.form['username'], request.form['password'])
       logged_user =ModelUser.login(mysql, user)
       if logged_user != None:
        if logged_user.password:
            login_user(logged_user)
            return redirect(url_for('Perfil'))
        else:
            flash("Invalid Password...")
            return render_template('login.html')
       else:
        flash("User not found...")
        return render_template("login.html")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/protected")
@login_required
def protected():
    return "<h1>Esta es una vista protegida, solo para usuarios autenticados<h1>"

def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1>Página no encontrada<h1>"


##################################
@app.route("/page")
@login_required
def Page():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM reservatabla')
    data = cur.fetchall()
    return render_template("index.html", procesos=data)


@app.route('/add_process', methods=['POST'])
def add_process():
    if request.method == 'POST':
        servicio = request.form['servicio']
        maquina = request.form['maquina']
        empresa = request.form['empresa']
        operador = request.form['operador']
        fecha = request.form['fecha']
        
        cur = mysql.connection.cursor()

        # Verificar si existe una reserva con los mismos valores de servicio, maquina, empresa, operador y fecha
        cur.execute('SELECT * FROM reservatabla WHERE servicio = %s AND maquina = %s AND empresa = %s AND operador = %s', (servicio, maquina, empresa, operador))
        existing_process = cur.fetchone()
        
        if existing_process:
            flash('Ya existe una reserva con el mismo servicio, máquina, empresa y operador')

            # Guardar los datos repetidos en la tabla reservas_repetidas
            cur.execute('INSERT INTO reservarepetidatabla (servicio_rep, maquina_rep, empresa_rep, operador_rep, fecha_rep) VALUES (%s, %s, %s, %s, %s)',
                        (servicio, maquina, empresa, operador, fecha))
            mysql.connection.commit()

            return redirect(url_for('Page'))

        cur.execute('INSERT INTO reservatabla (servicio, maquina, empresa, operador, fecha) VALUES (%s, %s, %s, %s, %s)',
                    (servicio, maquina, empresa, operador, fecha)) 
        mysql.connection.commit()
        flash('Reserva agregada satisfactoriamente')
        return redirect(url_for('Page'))

    
@app.route('/repeated_process_data')
def repeated_process_data():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM reservarepetidatabla')
    data = cur.fetchall()
    return render_template('repeated_process_data.html', procesos=data)



@app.route('/edit_process/<id>')
def get_process(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM reservatabla WHERE id = %s', (id,))
    data = cur.fetchall()
    return render_template('edit-process.html', procesos=data[0])

@app.route('/update_process/<id>', methods=['POST'])
def update_process(id):
    if request.method == 'POST':
        servicio = request.form['servicio']
        maquina = request.form['maquina']
        empresa = request.form['empresa']
        operador = request.form['operador']
        fecha = request.form['fecha']
        cur = mysql.connection.cursor()
        cur.execute("""UPDATE reservatabla 
        SET servicio = %s, 
            maquina = %s, 
            empresa = %s, 
            operador = %s,
            fecha = %s
            WHERE id = %s
            """, (servicio, maquina, empresa, operador, fecha, id))
        mysql.connection.commit()
        flash('Reserva actualizada correctamente')
        return redirect(url_for('Page'))



@app.route('/delete_process/<string:id>')
def delete_process(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM reservatabla WHERE id = %s', (id,))
    mysql.connection.commit()
    flash('Reserva eliminada correctamente')
    return redirect(url_for('Page'))


@app.route('/delete_process_repeated/<string:id>')
def delete_process_repeated(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM reservarepetidatabla WHERE idrep= {0}'.format(id))
    mysql.connection.commit()
    flash('Proceso removido correctamente')
    return redirect(url_for('repeated_process_data'))

@app.route("/buscar", methods=['GET', 'POST'])
@login_required
def buscador():
    if request.method == "POST":
        search_query = request.form['search_query']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM reservatabla WHERE servicio = %s OR maquina LIKE %s", (search_query, '%' + search_query + '%'))
        data = cur.fetchall()
        return render_template("busqueda.html", procesos=data, search_query=search_query)
    else:
        return render_template("busqueda.html")
    

@app.route("/maquinas")
def maquinas():
    cur = mysql.connection.cursor()
    cur.execute('SELECT DISTINCT maquina FROM reservatabla')
    maquinas = cur.fetchall()  # Obtener la lista de máquinas
    maquina_procesos = []  # Lista para almacenar las máquinas y sus procesos

    for maquina in maquinas:
        cur.execute('SELECT * FROM reservatabla WHERE maquina = %s', (maquina[0],))
        procesos = cur.fetchall()  # Obtener los procesos de la máquina
        maquina_procesos.append((maquina[0], procesos))

    return render_template("maquinas.html", maquina_procesos=maquina_procesos)



@app.route('/eliminar_datos_tabla', methods=['GET'])
def eliminar_datos_tabla():
    cur = mysql.connection.cursor()
    cur.execute('TRUNCATE TABLE procesotabla')
    mysql.connection.commit()
    flash('Los datos de la tabla se han eliminado.')
    return redirect(url_for('Page'))

########################
def generar_csv(data, nombre_archivo):
    with open(nombre_archivo, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)

@app.route("/exportar_csv")
def exportar_csv():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM reservatabla')
    data = cur.fetchall()  # Obtener los datos de la tabla

    nombre_archivo = "datos_csv.csv"  # Nombre del archivo CSV de salida

    generar_csv(data, nombre_archivo)  # Llama a la función de exportación

    # Devuelve el archivo CSV como una descarga
    return send_file(nombre_archivo, as_attachment=True)




if __name__ == '__main__':
    app.config.from_object(config['development'])
#csrf.init_app(app)
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run(debug=True, port=4000)