import os
import uuid
from flask import Flask, session,render_template,request, Response, redirect, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from db import db_init, db
from models import  User, Product
from datetime import datetime
from flask_session import Session
from helpers import login_required
from flask import send_file
from sqlalchemy import create_engine

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///items.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db_init(app)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#static file path
@app.route("/static/<path:path>")
def static_dir(path):
    return send_from_directory("static", path)

#signup as merchant
@app.route("/signup", methods=["GET","POST"])
def signup():
	if request.method=="POST":
		session.clear()
		password = request.form.get("password")
		repassword = request.form.get("repassword")
		if(password!=repassword):
			return render_template("error.html", message="Passwords do not match!")

		#hash password
		pw_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
		
		fullname = request.form.get("fullname")
		username = request.form.get("username")
		#store in database
		new_user =User(fullname=fullname,username=username,password=pw_hash)
		try:
			db.session.add(new_user)
			db.session.commit()
		except:
			return render_template("error.html", message="Username already exists!")
		return render_template("login.html", msg="Account created!")
	return render_template("signup.html")

#login as merchant
@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method=="POST":
		session.clear()
		username = request.form.get("username")
		password = request.form.get("password")
		result = User.query.filter_by(username=username).first()
		print(result)
		# Ensure username exists and password is correct
		if result == None or not check_password_hash(result.password, password):
			return render_template("error.html", message="Invalid username and/or password")
		# Remember which user has logged in
		session["username"] = result.username
		return redirect("/home")
	return render_template("login.html")

#logout
@app.route("/logout")
def logout():
	session.clear()
	return redirect("/login")

#view all products
@app.route("/")
def index():
	rows = Product.query.all()
	return render_template("index.html", rows=rows)

#view Remesas
@app.route('/remesas')
def remesas():
	rows = Product.query.filter_by(category="remesa").all()
	return render_template("remesas.html", rows=rows)

#Busqueda
@app.route("/busqueda", methods=["GET", "POST"])
def busqueda():
    categories = Product.query.with_entities(Product.category).distinct().all()

    if request.method == "POST":
        category = request.form.get('category')
        
        if category:
            rows = Product.query.filter_by(category=category).all()
        else:
            rows = []

        return render_template("busqueda.html", filtered_rows=rows, categories=[cat[0] for cat in categories])
    else:
        return render_template("busqueda.html", categories=[cat[0] for cat in categories])


#merchant home page to add new products and edit existing products
@app.route("/home", methods=["GET", "POST"], endpoint='home')
@login_required
def home():
	if request.method == "POST":
		image = request.files['image']
		filename = str(uuid.uuid1())+os.path.splitext(image.filename)[1]
		image.save(os.path.join("static/images", filename))
		category= request.form.get("category")
		name = request.form.get("pro_name")
		description = request.form.get("description")
		price_range = request.form.get("price_range")
		comments = request.form.get("comments")
		new_pro = Product(category=category,name=name,description=description,price_range=price_range,comments=comments, filename=filename, username=session['username'])
		db.session.add(new_pro)
		db.session.commit()
		rows = Product.query.all()
		return render_template("home.html", rows=rows, message="Product added")
	
	rows = Product.query.filter_by(username=session['username'])
	return render_template("home.html", rows=rows)


# descargar de base de datos
@app.route('/download_db')
def download_db():
    # Configuración de la base de datos
    db_path = 'instance/items.db'
    
    try:
        # Verificamos si el archivo existe
        if os.path.exists(db_path):
            # Preparamos el archivo para descarga
            return send_file(
                db_path,
                mimetype='application/x-sqlite3',
                as_attachment=True,
                download_name='items.db'
            )
        else:
            # Manejamos el caso en que el archivo no existe
            return render_template('error.html', message='No se encontró la base de datos para descargar.')
    except Exception as e:
        # Manejo de errores
        return render_template('error.html', message=f'Ocurrió un error al intentar descargar la base de datos: {str(e)}')


	
#when edit product option is selected this function is loaded
@app.route("/edit/<int:pro_id>", methods=["GET", "POST"], endpoint='edit')
@login_required
def edit(pro_id):
	#select only the editing product from db
	result = Product.query.filter_by(pro_id = pro_id).first()
	
	if request.method == "POST":
		if result:
			db.session.delete(result)
			db.session.commit()
		return render_template("home.html", message="Product edited")
	return render_template("edit.html", result=result)

if __name__ == '__main__':
  
    app.run(debug=True)
