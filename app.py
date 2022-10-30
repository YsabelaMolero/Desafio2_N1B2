from unicodedata import name
from flask import Flask, render_template, url_for, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import datetime

app = Flask(__name__)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

class Func(db.Model):
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150))
    descrition = db.Column(db.String(280))  
    re = db.Column(db.Integer)

    def __init__(self, name, descrition, re):
        self.name = name
        self.descrition = descrition
        self.re = re

class Feedback(db.Model):
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    funcId = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.String(10000))
    metas = db.Column(db.String(1000)) 

    def __init__(self, funcId, feedback, metas) -> None:
        self.funcId = funcId
        self.feedback = feedback
        self.metas = metas

class Cargo(db.Model):
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150))
    descrition = db.Column(db.String(280))
    dataPromocao = db.Column(db.Date())   
    funcId = db.Column(db.Integer, nullable=False)   

    def __init__(self, name, descrition, dataPromocao, funcId) -> None:
        datePromo = str(dataPromocao).split('-')
        self.name = name
        self.descrition = descrition
        self.dataPromocao = datetime.date(int(datePromo[0]), int(datePromo[1]), int(datePromo[2]))
        self.funcId = funcId

class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Cadastrar')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'Esse usuário já existe. Por favor escolha outro.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    funcs = Func.query.all()
    return render_template('dashboard.html', funcs=funcs)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    func = Func.query.get(id)
    if request.method == 'POST':
        func.name = request.form['name']
        func.descrition = request.form['descrition']
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('edit.html', func=func)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def cadastro():
    if request.method == 'POST':
        try:
            func = Func(
                        name=request.form['name'],
                        descrition=request.form['descrition'],
                        re=request.form['re']
                    )
            db.session.add(func)
            db.session.commit()
            return redirect(url_for('dashboard'))
        except:
            db.session.rollback()
        finally:
            db.session.close()
    return render_template('cadastro.html')

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    try:
        func = Func.query.get(id)
        db.session.delete(func)
        db.session.commit()
        return redirect(url_for('dashboard'))
    except:
        db.session.rollback()
    finally:
        db.session.close()

@app.route('/view/<int:id>')
@login_required
def view(id):
    try:
        cargos = Cargo.query.filter_by(funcId=id).all()
        feeds = Feedback.query.filter_by(funcId=id).all()
        func = Func.query.get(id)
        return render_template('view.html', func=func, cargos=cargos, feeds=feeds)
    except:
        return redirect(url_for('dashboard'))

@app.route('/addCargo/<int:id>',  methods=['GET', 'POST'])
@login_required
def addCargo(id):
    if request.method == 'POST':
        print('>>>>>>>> '+ request.form['dataPromocao'])
        try:
            new_cargo = Cargo(name=request.form['name'],
                            descrition=request.form['descrition'],
                            dataPromocao=request.form['dataPromocao'],
                            funcId=id
                        )
            db.session.add(new_cargo)
            db.session.commit()     
            view(id)      
            return redirect(url_for('view', id = id))
        # except:
        #     db.session.rollback()
        finally:
            db.session.close()
            
    return redirect(url_for('view', id = id))
    #return view(id)

@app.route('/deleteCargo/<int:id>/<int:idFunc>', methods=['GET', 'POST'])
@login_required
def deleteCargo(id, idFunc):
    if request.method == 'POST':
        try:
            cargo = Cargo.query.get(id)
            db.session.delete(cargo)
            db.session.commit()
            # view(id)
            return redirect(url_for('view', id = idFunc))
        except:
            db.session.rollback()
        finally:
            db.session.close()
            
    # return view(id)
    return redirect(url_for('view', id = idFunc))

@app.route('/addFeed/<int:id>',  methods=['GET', 'POST'])
@login_required
def addFeed(id):
    if request.method == 'POST':
        try:
            new_feed = Feedback(feedback=request.form['feedback'],
                            metas=request.form['metas'],
                            funcId=id
                        )
            db.session.add(new_feed)
            db.session.commit()     
            view(id)      
            return redirect(url_for('view', id = id))
        except:
            db.session.rollback()
        finally:
            db.session.close()
            
    return redirect(url_for('view', id = id))
    #return view(id)

@app.route('/deleteFeed/<int:id>/<int:idFunc>', methods=['GET', 'POST'])
@login_required
def deleteFeed(id, idFunc):
    if request.method == 'POST':
        try:
            feed = Feedback.query.get(id)
            db.session.delete(feed)
            db.session.commit()
            # view(id)
            return redirect(url_for('view', id = idFunc))
        except:
            db.session.rollback()
        finally:
            db.session.close()
            
    # return view(id)
    return redirect(url_for('view', id = idFunc))

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
