from flask import Flask, render_template, request, redirect, url_for,session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail,Message

app=Flask(__name__)
app.secret_key="123abc"
# ------------------------------------------------------
# Mail Configuration
# ------------------------------------------------------
# Mail Configuration (FIXED)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'raparlasivabharath21@gmail.com'
app.config['MAIL_PASSWORD'] = 'zcaiiwurqdqqxlra'  # no spaces
app.config['MAIL_DEFAULT_SENDER'] = 'raparlasivabharath21@gmail.com'
mail=Mail(app)
serializer=URLSafeTimedSerializer(app.secret_key)
# ------------------------------------------------------
# Password Reset Token Functions
def generate_reset_token(email):
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):
    try:
        email = serializer.loads(
            token,
            salt='password-reset-salt',
            max_age=expiration
        )
    except:
        return None
    return email
#---------------------------------------------------------
# Database Configuration
def get_db():
    return sqlite3.connect("database.db", check_same_thread=False)

# Registration Route
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        firstname=request.form['firstname']
        lastname=request.form['lastname']
        email=request.form['email']
        password=generate_password_hash(request.form['password'])
        db=get_db()
        cursor=db.cursor()
        try:
            cursor.execute(
                "insert into user1 (firstname, lastname, email, password) values (?, ?, ?, ?)",
                (firstname, lastname,email,password)
                )
            db.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except:
            flash("Username or Email already exists. Please Login.")
            return redirect(url_for('login'))
        finally:
            cursor.close()
            db.close()
            
    return render_template('register.html')
# Login Route
@app.route('/',methods=['GET','POST'])
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        db=get_db()
        cursor=db.cursor()
        cursor.row_factory=sqlite3.Row
        cursor.execute("select * from user1 where email=?",(email,))
        user=cursor.fetchone()
        cursor.close()
        db.close()
        if user and check_password_hash(user['password'],password):
            session['user_id']=user['id']
            session['firstname']=user['firstname']
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')
#about route
@app.route('/about')
def about():
    return render_template('about.html')

# logout Route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Dashboard Route
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('login'))
    db=get_db()
    cursor=db.cursor()
    cursor.row_factory=sqlite3.Row
    cursor.execute("select * from notes where user_id=? order by created_at desc",
                   (session['user_id'],))
    notes=cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('dashboard.html',notes=notes)

# Add Note Route
@app.route('/add',methods=['GET','POST'])
def add_note():
    if 'user_id' not in session:
        flash("Please log in to add notes.", "warning")
        return redirect(url_for('login'))
    if request.method=='POST':
        title=request.form['title']
        content=request.form['content']
        db=get_db()
        cursor=db.cursor()
        cursor.execute(
            "insert into notes (user_id,title,content) values (?,?,?)",
            (session['user_id'],title,content)
            )
        db.commit()
        cursor.close()
        db.close()
        flash("Note added successfully!", "success")
        return redirect(url_for('dashboard'))
    return render_template('add_note.html')
# Delete Note Route
@app.route('/delete_note/<int:note_id>')
def delete_note(note_id):
    if 'user_id' not in session:
        flash("Please log in to delete notes.", "warning")
        return redirect(url_for('login'))
    db=get_db()
    cursor=db.cursor()
    cursor.execute(
        "delete from notes where id=? and user_id=?",
        (note_id,session['user_id'])
        )
    db.commit()
    cursor.close()
    db.close()
    flash("Note deleted successfully!", "success")
    return redirect(url_for('dashboard'))

#Edit note route 
@app.route('/edit_note/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    if 'user_id' not in session:
        flash("Please log in to edit notes.", "warning")
        return redirect(url_for('login'))
    db=get_db()
    cursor = db.cursor()
    cursor.row_factory = sqlite3.Row
    if request.method == 'POST':
        content = request.form['content']
        cursor.execute(
            "update notes set content=? where id=? and user_id=?",
            (content, note_id, session['user_id'])
        )
        db.commit()
        cursor.close()
        db.close()
        flash("Note updated successfully!", "success")
        return redirect(url_for('dashboard'))
    else:
        cursor.execute(
            "select * from notes where id=? and user_id=?",
            (note_id, session['user_id'])
        )
        note = cursor.fetchone()
        cursor.close()
        db.close()
        if note:
            return render_template('edit_note.html', note=note)
        else:
            flash("Note not found.", "danger")
            return redirect(url_for('dashboard'))
        
        
        
        
        
#Forgot Password Route
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        db= get_db()

        cursor = db.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute("SELECT * FROM user1 WHERE email=?", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            token = generate_reset_token(email)
            reset_link = url_for(
                'reset_with_token',
                token=token,
                _external=True
            )

            msg = Message(
                "Password Reset Request",
                recipients=[email]
            )
            msg.body = f"""
Hello,

Click the link below to reset your password:
{reset_link}

This link expires in 1 hour.

If you did not request this, ignore this email.
"""
            mail.send(msg)

        flash(" Reset link has been sent to Email Successfuly!!.")
        return redirect(url_for('login'))

    return render_template('forgot_password.html')


# Password Reset Route
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    email = verify_reset_token(token)

    if not email:
        flash("Invalid or expired link")
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = generate_password_hash(request.form['password'])
        
        db=get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE user1 SET password=? WHERE email=?",
            (new_password, email)
        )
        db.commit()
        cursor.close()
        db.close()

        flash("Password reset successful. Please login.")
        return redirect(url_for('login'))

    return render_template('reset_with_token.html')


#search route
@app.route('/search')
def search_notes():
    if 'user_id' not in session:
        flash("Please log in to search notes.", "warning")
        return redirect(url_for('login'))

    query = request.args.get('query', '').strip()
    db= get_db()

    cursor = db.cursor()
    cursor.row_factory = sqlite3.Row

    if query:
        cursor.execute(
            """
            SELECT * FROM notes
            WHERE user_id = ? AND title LIKE ?
            ORDER BY created_at DESC
            """,
            (session['user_id'], f"%{query}%")
        )
    else:
        cursor.execute(
            """
            SELECT * FROM notes
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (session['user_id'],)
        )

    notes = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('dashboard.html', notes=notes)

# profile route

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("Please login to view your profile.", "warning")
        return redirect(url_for('login'))
    
    db= get_db()
    cursor = db.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute(
        "SELECT firstname, lastname, email FROM user1 WHERE id=?",
        (session['user_id'],)
    )
    user = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template('profile.html', user=user)

#edit profile route

@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash("Please login to edit profile.", "warning")
        return redirect(url_for('login'))
    db=get_db()

    cursor = db.cursor()
    cursor.row_factory = sqlite3.Row

    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']

        cursor.execute(
            """
            UPDATE user1
            SET firstname=?, lastname=?, email=?
            WHERE id=?
            """,
            (firstname, lastname, email, session['user_id'])
        )
        db.commit()
        cursor.close()
        

        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))

    cursor.execute(
        "SELECT firstname, lastname, email FROM user1 WHERE id=?",
        (session['user_id'],)
    )
    user = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template('edit_profile.html', user=user)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        db= get_db()

        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO contact_messages (name, email, message)
            VALUES (?, ?, ?)
            """,
            (name, email, message)
        )
        db.commit()
        cursor.close()
        db.close()

        flash("Your message has been sent successfully!", "success")
        return redirect(url_for('contact'))

    return render_template('contact.html')


if __name__=='__main__':
    app.run(debug=True)      
                
     