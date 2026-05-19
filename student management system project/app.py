from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secretkey"

# =========================
# DATABASE CONNECTION
# =========================

def get_db_connection():

    conn = sqlite3.connect("student.db", timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # ENABLE FOREIGN KEY
    conn.execute("PRAGMA foreign_keys = ON")

    return conn

# =========================
# CREATE TABLES
# =========================

def init_db():

    conn = get_db_connection()

    cursor = conn.cursor()

    # STUDENTS TABLE
    #added a new collom of sudents is registerr_number, dob, address, phone and aadhaar

    cursor.execute("""
CREATE TABLE IF NOT EXISTS students (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT,

    roll_number TEXT,

    department TEXT,

    email TEXT,

    course TEXT,

    gender TEXT,

    register_number TEXT,

    address TEXT,

    dob TEXT,

    phone TEXT,

    aadhaar TEXT

)
""")

    # EDUCATION TABLE

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS education (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        student_id INTEGER,              

        standard TEXT,

        year TEXT,

        school_college TEXT,

        marks TEXT,

        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE

    )
    """)

    conn.commit()

    conn.close()
# =========================
# HOME
# =========================

@app.route('/')
def home():
    return render_template('home.html')

# =========================
# REGISTER
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']

        email = request.form['email']

        confirm_email = request.form['confirm_email']

        password = generate_password_hash(
            request.form['password']
        )

        # EMAIL CHECK
        if email != confirm_email:

            flash("Emails do not match")

            return redirect(url_for('register'))

        conn = get_db_connection()
        cursor = conn.cursor()

        # CHECK EXISTING EMAIL
        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            flash("Email already exists")

            conn.close()

            return redirect(url_for('register'))

        # INSERT USER
        cursor.execute("""
        INSERT INTO users (username, email, password)
        VALUES (?, ?, ?)
        """, (username, email, password))

        conn.commit()
        conn.close()

        flash("Registration Successful")

        return redirect(url_for('login'))

    return render_template('register.html')

# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user['password'], password):

            session['user_id'] = user['id']
            session['username'] = user['username']

            return redirect(url_for('dashboard'))

        else:
            flash("Invalid Email or Password")

    return render_template('login.html')

# =========================
# RESET PASSWORD
# =========================

@app.route('/reset', methods=['GET', 'POST'])
def reset():

    if request.method == 'POST':

        email = request.form['email']
        new_password = generate_password_hash(request.form['password'])

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE users
        SET password = ?
        WHERE email = ?
        """, (new_password, email))

        conn.commit()
        conn.close()

        flash("Password Updated")

        return redirect(url_for('login'))

    return render_template('reset.html')

# =========================
# DASHBOARD
# =========================

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    search = request.args.get('search', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    if search:

        cursor.execute("""
        SELECT * FROM students
        WHERE name LIKE ?
        """, ('%' + search + '%',))

    else:

        cursor.execute("SELECT * FROM students")

    students = cursor.fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        students=students
    )

# =========================
# ADD STUDENT
# =========================

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():

    if request.method == 'POST':

        conn = get_db_connection()
        cursor = conn.cursor()

        # STUDENT DETAILS

        name = request.form['name']
        roll_number = request.form['roll_number']
        department = request.form['department']
        email = request.form['email']
        course = request.form['course']
        gender = request.form['gender']
        register_number = request.form['register_number']
        dob = request.form['dob']
        address = request.form['address']
        phone = request.form['phone']
        aadhaar = request.form['aadhaar']

        # INSERT STUDENT

        cursor.execute("""
        INSERT INTO students
        (
            name,
            roll_number,
            department,
            email,
            course,
            gender,
            register_number,
            dob,
            address,
            phone,
            aadhaar
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            roll_number,
            department,
            email,
            course,
            gender,
            register_number,
            dob,
            address,
            phone,
            aadhaar
        ))

        student_id = cursor.lastrowid

        # EDUCATION DETAILS

        standards = request.form.getlist('standard')
        years = request.form.getlist('year')
        schools = request.form.getlist('school_college')
        marks = request.form.getlist('marks')

        # INSERT TABLE ROWS

        for i in range(len(standards)):

            if standards[i] != "":

                cursor.execute("""
                INSERT INTO education
                (
                    student_id,
                    standard,
                    year,
                    school_college,
                    marks
                )

                VALUES (?, ?, ?, ?, ?)
                """, (
                    student_id,
                    standards[i],
                    years[i],
                    schools[i],
                    marks[i]
                ))

        conn.commit()
        conn.close()

        flash("Student Added Successfully")

        return redirect(url_for('dashboard'))

    return render_template('add_student.html')

# =========================
# VIEW STUDENT
# =========================

@app.route('/student/<int:id>')
def student_view(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    # GET STUDENT

    cursor.execute("""
    SELECT * FROM students
    WHERE id = ?
    """, (id,))

    student = cursor.fetchone()

    # GET EDUCATION DETAILS

    cursor.execute("""
    SELECT * FROM education
    WHERE student_id = ?
    """, (id,))

    education = cursor.fetchall()

    conn.close()

    return render_template(
        'student_view.html',
        student=student,
        education=education
    )
# =========================
# EDIT STUDENT
# =========================
@app.route('/edit_student/<int:id>', methods=['GET', 'POST'])
def edit_student(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':

        # STUDENT DETAILS

        name = request.form['name']
        roll_number = request.form['roll_number']
        department = request.form['department']
        email = request.form['email']
        course = request.form['course']
        gender = request.form['gender']
        register_number = request.form['register_number']
        dob = request.form['dob']
        address = request.form['address']
        phone = request.form['phone']
        aadhaar = request.form['aadhaar']

        # UPDATE STUDENT TABLE

        cursor.execute("""
        UPDATE students
        SET
            name = ?,
            roll_number = ?,
            department = ?,
            email = ?,
            course = ?,
            gender = ?,
            register_number = ?,
            dob = ?,    
            address = ?,
            phone = ?,
            aadhaar = ?
        WHERE id = ?
        """, (
            name,
            roll_number,
            department,
            email,
            course,
            gender,
            register_number,
            dob,
            address,
            phone,
            aadhaar,
            id
        ))

        # DELETE OLD EDUCATION DETAILS

        cursor.execute("""
        DELETE FROM education
        WHERE student_id = ?
        """, (id,))

        # GET NEW EDUCATION DETAILS

        standards = request.form.getlist('standard')
        years = request.form.getlist('year')
        schools = request.form.getlist('school_college')
        marks = request.form.getlist('marks')

        # INSERT UPDATED EDUCATION DETAILS

        for i in range(len(standards)):

            if standards[i] != "":

                cursor.execute("""
                INSERT INTO education
                (
                    student_id,
                    standard,
                    year,
                    school_college,
                    marks
                )

                VALUES (?, ?, ?, ?, ?)
                """, (
                    id,
                    standards[i],
                    years[i],
                    schools[i],
                    marks[i]
                ))

        conn.commit()
        conn.close()

        flash("Student Updated Successfully")

        return redirect(url_for('dashboard'))

    # GET STUDENT DATA

    cursor.execute("""
    SELECT * FROM students
    WHERE id = ?
    """, (id,))

    student = cursor.fetchone()

    # GET EDUCATION DATA

    cursor.execute("""
    SELECT * FROM education
    WHERE student_id = ?
    """, (id,))

    education = cursor.fetchall()

    conn.close()

    return render_template(
        'edit_student.html',
        student=student,
        education=education
    )

# =========================
# DELETE STUDENT
# =========================

@app.route('/delete_student/<int:id>')
def delete_student(id):

    conn = get_db_connection()

    cursor = conn.cursor()

    # DELETE EDUCATION DETAILS FIRST
    cursor.execute(
        "DELETE FROM education WHERE student_id = ?",
        (id,)
    )

    # DELETE STUDENT
    cursor.execute(
        "DELETE FROM students WHERE id = ?",
        (id,)
    )

    conn.commit()

    conn.close()

    flash("Student Deleted Successfully")

    return redirect(url_for('dashboard'))
# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))

# =========================
# MAIN
# =========================

if __name__ == '__main__':

    init_db()

    app.run(debug=True, use_reloader=False)