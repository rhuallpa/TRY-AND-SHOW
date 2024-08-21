import os
import pdfplumber
from flask import Flask, request, redirect, url_for, render_template, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.config['EXTRACTED_DATA'] = []  # Para almacenar los datos extraídos globalmente

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_data_from_pdf(pdf_path):
    extracted_data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                data = {
                    'Nombre de la Localidad': 'N/A',
                    'Latitud': 'N/A',
                    'Longitud': 'N/A',
                    'Calle/Av. Pasaje, etc.': 'N/A',
                    'Distrito': 'N/A',
                    'Provincia': 'N/A',
                    'Departamento': 'N/A',
                    'Encargado': 'N/A'
                }
                
                for line in lines:
                    if 'Latitud' in line:
                        data['Latitud'] = line.split(':')[1].strip()
                    if 'Longitud' in line:
                        data['Longitud'] = line.split(':')[1].strip()
                    if 'Nombre de la Localidad' in line:
                        data['Nombre de la Localidad'] = line.split(':')[1].strip()
                    if 'Calle/Av. Pasaje, etc.' in line or 'Calle/Av. etc.' in line:
                        data['Calle/Av. Pasaje, etc.'] = line.split(':')[1].strip()
                    if 'Distrito' in line:
                        data['Distrito'] = line.split(':')[1].strip()
                    if 'Provincia' in line:
                        data['Provincia'] = line.split(':')[1].strip()
                    if 'Departamento' in line:
                        data['Departamento'] = line.split(':')[1].strip()
                    if 'Encargado' in line:
                        data['Encargado'] = line.split(':')[1].strip()
                
                if data['Nombre de la Localidad'] != 'N/A' and data['Latitud'] != 'N/A' and data['Longitud'] != 'N/A':
                    extracted_data.append(data)
    
    return extracted_data


def filter_data(data, filters):
    filtered_data = []
    for item in data:
        match = True
        for key, value in filters.items():
            if value and value.lower() not in item[key].lower():
                match = False
                break
        if match:
            filtered_data.append(item)
    return filtered_data

@app.route('/', methods=['GET', 'POST'])
def index():
    data = []
    
    if request.method == 'POST':
        if 'pdf' not in request.files:
            return redirect(request.url)
        file = request.files['pdf']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            app.config['EXTRACTED_DATA'] = extract_data_from_pdf(file_path)
    
    # Procesar filtros de búsqueda
    filters = {
        'Nombre de la Localidad': request.args.get('localidad', ''),
        'Distrito': request.args.get('distrito', ''),
        'Provincia': request.args.get('provincia', ''),
        'Departamento': request.args.get('departamento', '')
    }
    
    data = filter_data(app.config['EXTRACTED_DATA'], filters)
    
    return render_template('index.html', data=data)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
