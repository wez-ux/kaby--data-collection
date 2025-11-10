from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    """Connexion DB adaptée pour Render"""
    if 'RENDER' in os.environ:
        # Sur Render, on utilise un chemin persistant
        db_path = '/opt/render/project/src/dictionnaire_kabye.db'
    else:
        # En local
        db_path = 'dictionnaire_kabye.db'
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialisation de la base de données"""
    conn = get_db_connection()
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
    
    # Exemples initiaux
    c.execute('SELECT COUNT(*) FROM mots_kabye')
    if c.fetchone()[0] == 0:
        exemples = [
            ('aalayu', '[âlâyú]', 'qui sera le premier', 'nom', 'Aalayu tem qui sera le premier à finir', 'Admin'),
            ('abaa', '[ábaa]', 'exprime la pitié, innocence', 'interjection', 'Pakpa-u hayu abaa yem', 'Admin'),
            ('ɛ', '[ɛ]', 'voyère mi-ouverte antérieure non arrondie', 'lettre', '', 'Système')
        ]
        c.executemany('''
            INSERT INTO mots_kabye (mot_kabye, api, traduction_francaise, categorie_grammaticale, exemple_usage, verifie_par)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', exemples)
    
    conn.commit()
    conn.close()

@app.route('/')
def accueil():
    return render_template('formulaire.html')

@app.route('/sauvegarder', methods=['POST'])
def sauvegarder():
    try:
        data = request.get_json()
        
        if not data.get('mot_kabye') or not data.get('traduction_francaise'):
            return jsonify({'success': False, 'error': 'Mot kabyè et traduction obligatoires'})
        
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO mots_kabye 
            (mot_kabye, api, traduction_francaise, categorie_grammaticale, exemple_usage, verifie_par)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['mot_kabye'].strip(),
            data.get('api', '').strip(),
            data['traduction_francaise'].strip(),
            data.get('categorie_grammaticale', '').strip(),
            data.get('exemple_usage', '').strip(),
            data.get('verifie_par', 'Anonyme').strip()
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'✅ Mot "{data["mot_kabye"]}" sauvegardé !'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/mots')
def liste_mots():
    """Voir tous les mots"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM mots_kabye ORDER BY date_ajout DESC')
    mots = c.fetchall()
    conn.close()
    
    return render_template('liste_mots.html', mots=mots)

@app.route('/api/mots')
def api_mots():
    """API pour récupérer les mots en JSON"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM mots_kabye ORDER BY mot_kabye')
    mots = c.fetchall()
    conn.close()
    
    mots_list = []
    for mot in mots:
        mots_list.append(dict(mot))
    
    return jsonify(mots_list)

# Initialisation au démarrage
init_db()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)