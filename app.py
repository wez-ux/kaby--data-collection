from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# Stockage simple en mémoire
donnees = {
    "mots": [
        {
            "id": 1,
            "mot_kabye": "aalayu",
            "api": "[âlâyú]",
            "traduction_francaise": "qui sera le premier",
            "categorie_grammaticale": "nom",
            "exemple_usage": "Aalayu tem qui sera le premier à finir",
            "verifie_par": "Admin",
            "date_ajout": "2024-01-15 10:00:00"
        },
        {
            "id": 2,
            "mot_kabye": "abaa",
            "api": "[ábaa]",
            "traduction_francaise": "exprime la pitié, l'innocence, l'agacement",
            "categorie_grammaticale": "interjection",
            "exemple_usage": "Pakpa-u hayu abaa yem",
            "verifie_par": "Admin",
            "date_ajout": "2024-01-15 10:05:00"
        }
    ],
    "prochain_id": 3
}

@app.route('/')
def accueil():
    return render_template('formulaire.html')

@app.route('/sauvegarder', methods=['POST'])
def sauvegarder_mot():
    try:
        data = request.get_json()
        
        if not data.get('mot_kabye') or not data.get('traduction_francaise'):
            return jsonify({'success': False, 'error': 'Mot kabyè et traduction française sont obligatoires'})
        
        # Vérifier si le mot existe déjà
        mot_existe = any(mot['mot_kabye'].lower() == data['mot_kabye'].lower() 
                        for mot in donnees['mots'])
        
        if mot_existe:
            return jsonify({'success': False, 'error': 'Ce mot existe déjà dans le dictionnaire'})
        
        # Créer le nouveau mot
        nouveau_mot = {
            "id": donnees['prochain_id'],
            "mot_kabye": data['mot_kabye'].strip(),
            "api": data.get('api', '').strip(),
            "traduction_francaise": data['traduction_francaise'].strip(),
            "categorie_grammaticale": data.get('categorie_grammaticale', '').strip(),
            "exemple_usage": data.get('exemple_usage', '').strip(),
            "verifie_par": data.get('verifie_par', 'Anonyme').strip(),
            "date_ajout": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Ajouter le mot
        donnees['mots'].append(nouveau_mot)
        donnees['prochain_id'] += 1
        
        return jsonify({
            'success': True, 
            'message': f'✅ Mot "{data["mot_kabye"]}" sauvegardé ! (Données en mémoire)'
        })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/mots')
def liste_mots():
    mots_tries = sorted(donnees['mots'], key=lambda x: x['mot_kabye'])
    return render_template('liste_mots.html', mots=mots_tries)

@app.route('/api/mots')
def api_mots():
    return jsonify(donnees['mots'])

@app.route('/santé')
def santé():
    return jsonify({'status': 'OK', 'total_mots': len(donnees['mots'])})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)