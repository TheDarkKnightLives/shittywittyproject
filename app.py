from flask import Flask, request, redirect, url_for, render_template, session, send_file, flash
from werkzeug.utils import secure_filename
import pandas as pd
import sqlite3
import os
import zipfile
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the database
def init_db():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            email TEXT,
            name TEXT,
            rollno TEXT,
            phone TEXT,
            on_campus TEXT,
            off_campus TEXT,
            package TEXT,
            course_name TEXT,
            college_name TEXT,
            company_name TEXT,
            annual_turnover TEXT,
            image TEXT,
            pdf TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def student_form():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        rollno = request.form.get('rollno')
        phone = request.form.get('phone')
        on_campus = request.form.get('on_campus')
        off_campus = request.form.get('off_campus')
        package = request.form.get('package')
        course_name = request.form.get('course_name')
        college_name = request.form.get('college_name')
        company_name = request.form.get('company_name')
        annual_turnover = request.form.get('annual_turnover')

        # Handle file uploads
        image_file = request.files.get('evidence_image')
        pdf_file = request.files.get('evidence_pdf')

        if image_file and image_file.filename:
            image_filename = secure_filename(f"{rollno}.jpg")
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(image_path)
        else:
            image_filename = None

        if pdf_file and pdf_file.filename:
            pdf_filename = secure_filename(f"{rollno}_doc.pdf")
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
            pdf_file.save(pdf_path)
        else:
            pdf_filename = None

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (email, name, rollno, phone, on_campus, off_campus, package, course_name, college_name, company_name, annual_turnover, image, pdf) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (email, name, rollno, phone, on_campus, off_campus, package, course_name, college_name, company_name, annual_turnover, image_filename, pdf_filename))
        conn.commit()
        conn.close()

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

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    students_data = cursor.fetchall()
    conn.close()
    return render_template('upload.html', students=students_data)

@app.route('/export_students')
def export_students():
    if 'username' not in session:
        flash('You need to login first.', 'warning')
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    data = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(data, columns=['Email', 'Name', 'Rollno', 'Phone', 'On Campus', 'Off Campus', 'Package', 'Course Name', 'College Name', 'Company Name', 'Annual Turnover', 'Image', 'PDF'])
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'students.xlsx')
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)

@app.route('/download_files')
def download_files():
    if 'username' not in session:
        flash('You need to login first.', 'warning')
        return redirect(url_for('login'))
    
    # Define a path for the ZIP file
    zip_filename = 'files.zip'
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)

    # Create a ZIP file
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # Add image files
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if filename.endswith('.jpg'):
                zipf.write(os.path.join(app.config['UPLOAD_FOLDER'], filename), filename)
            elif filename.endswith('.pdf'):
                zipf.write(os.path.join(app.config['UPLOAD_FOLDER'], filename), filename)

    return send_file(zip_path, as_attachment=True, download_name=zip_filename)

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000)
