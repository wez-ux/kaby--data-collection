from flask import Flask, render_template, request, jsonify
import sqlite3
import csv
import os

app = Flask(__name__)

# Initialisation de la base de données
def init_db():
    conn = sqlite3.connect('dictionnaire_kabye.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS mots_kabye (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mot_kabye TEXT NOT NULL,
            api TEXT,
            traduction_francaise TEXT NOT NULL,
            categorie_grammaticale TEXT,
            exemple_usage TEXT,
            verifie_par TEXT,
            date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def formulaire():
    return render_template('formulaire.html')

@app.route('/sauvegarder', methods=['POST'])
def sauvegarder():
    try:
        data = request.json
        
        conn = sqlite3.connect('dictionnaire_kabye.db')
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO mots_kabye 
            (mot_kabye, api, traduction_francaise, categorie_grammaticale, exemple_usage, verifie_par)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['mot_kabye'],
            data['api'],
            data['traduction_francaise'],
            data['categorie_grammaticale'],
            data['exemple_usage'],
            data['verifie_par']
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Mot sauvegardé !'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/export-csv')
def export_csv():
    conn = sqlite3.connect('dictionnaire_kabye.db')
    c = conn.cursor()
    c.execute('SELECT * FROM mots_kabye')
    mots = c.fetchall()
    conn.close()
    
    # Création du CSV
    with open('dictionnaire_contributions.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Mot Kabyè', 'API', 'Traduction', 'Catégorie', 'Exemple', 'Vérifié par', 'Date'])
        writer.writerows(mots)
    
    return jsonify({'success': True, 'message': 'CSV exporté !'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)