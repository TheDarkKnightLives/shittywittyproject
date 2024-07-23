from flask import Flask, request, redirect, url_for, render_template, session, send_file, flash
from werkzeug.utils import secure_filename
import pandas as pd
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the database
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS students
                  (email TEXT, name TEXT, rollno TEXT, phone TEXT, department TEXT, batch TEXT)''')
conn.commit()

@app.route('/', methods=['GET', 'POST'])
def student_form():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['username']
        rollno = request.form['rno']
        phone = request.form['phn']
        department = request.form['dpt']
        batch = request.form['btch']
        
        cursor.execute("INSERT INTO students (email, name, rollno, phone, department, batch) VALUES (?, ?, ?, ?, ?, ?)",
                       (email, name, rollno, phone, department, batch))
        conn.commit()
        flash('Form submitted successfully!', 'success')
        return redirect(url_for('student_form'))

    return render_template('student_form.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'chumma' and password == 'chumma':
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('upload_file'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'username' not in session:
        flash('You need to login first.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        files = request.files.getlist('files')
        dfs = []
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                if filename.endswith('.csv'):
                    dfs.append(pd.read_csv(file_path))
                elif filename.endswith('.xlsx'):
                    dfs.append(pd.read_excel(file_path))
        
        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            combined_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'combined.xlsx')
            combined_df.to_excel(combined_file_path, index=False)
            return send_file(combined_file_path, as_attachment=True)

    cursor.execute("SELECT * FROM students")
    students_data = cursor.fetchall()
    return render_template('upload.html', students=students_data)

@app.route('/export_students')
def export_students():
    if 'username' not in session:
        flash('You need to login first.', 'warning')
        return redirect(url_for('login'))

    cursor.execute("SELECT * FROM students")
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=['Email', 'Name', 'Rollno', 'Phone', 'Department', 'Batch'])
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'students.xlsx')
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
