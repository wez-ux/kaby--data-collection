from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Configuration Vercel KV
KV_KEY = "mots_kabye"

# Import conditionnel pour Vercel KV
try:
    from vercel_kv import kv
    KV_AVAILABLE = True
    print("✅ Vercel KV disponible")
except ImportError:
    KV_AVAILABLE = False
    print("❌ Vercel KV non disponible - mode mémoire activé")

def initialiser_donnees_par_defaut():
    """Données par défaut"""
    return {
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
            },
            {
                "id": 3,
                "mot_kabye": "ɛ",
                "api": "[ɛ]",
                "traduction_francaise": "voyelle mi-ouverte antérieure non arrondie",
                "categorie_grammaticale": "lettre",
                "exemple_usage": "",
                "verifie_par": "Système",
                "date_ajout": "2024-01-15 10:10:00"
            }
        ],
        "prochain_id": 4
    }

# Stockage en mémoire de secours
donnees_memoire = initialiser_donnees_par_defaut()

async def charger_donnees():
    """Charger les données depuis Vercel KV ou mémoire"""
    if KV_AVAILABLE:
        try:
            data = await kv.get(KV_KEY)
            if data:
                print("✅ Données chargées depuis Vercel KV")
                return json.loads(data)
            else:
                # Initialiser KV avec les données par défaut
                donnees_defaut = initialiser_donnees_par_defaut()
                await kv.set(KV_KEY, json.dumps(donnees_defaut))
                print("✅ Données initialisées dans Vercel KV")
                return donnees_defaut
        except Exception as e:
            print(f"❌ Erreur Vercel KV: {e}")
            return donnees_memoire
    else:
        print("📝 Mode mémoire activé")
        return donnees_memoire

async def sauvegarder_donnees(donnees):
    """Sauvegarder les données dans Vercel KV ou mémoire"""
    if KV_AVAILABLE:
        try:
            await kv.set(KV_KEY, json.dumps(donnees))
            print("✅ Données sauvegardées dans Vercel KV")
            return True
        except Exception as e:
            print(f"❌ Erreur sauvegarde Vercel KV: {e}")
            return False
    else:
        # Mode mémoire
        global donnees_memoire
        donnees_memoire = donnees
        print("📝 Données sauvegardées en mémoire")
        return True

@app.route('/')
def accueil():
    return render_template('formulaire.html')

@app.route('/sauvegarder', methods=['POST'])
async def sauvegarder_mot():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('mot_kabye') or not data.get('traduction_francaise'):
            return jsonify({'success': False, 'error': 'Mot kabyè et traduction française sont obligatoires'})
        
        # Charger les données existantes
        donnees = await charger_donnees()
        
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
        
        # Ajouter le mot et mettre à jour l'ID
        donnees['mots'].append(nouveau_mot)
        donnees['prochain_id'] += 1
        
        # Sauvegarder
        if await sauvegarder_donnees(donnees):
            return jsonify({
                'success': True, 
                'message': f'✅ Mot "{data["mot_kabye"]}" sauvegardé avec succès !'
            })
        else:
            return jsonify({'success': False, 'error': 'Erreur lors de la sauvegarde'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/mots')
async def liste_mots():
    """Afficher tous les mots"""
    donnees = await charger_donnees()
    mots = donnees['mots']
    
    # Trier par mot kabyè
    mots_tries = sorted(mots, key=lambda x: x['mot_kabye'])
    
    return render_template('liste_mots.html', mots=mots_tries)

@app.route('/api/mots')
async def api_mots():
    """API pour récupérer les mots en JSON"""
    donnees = await charger_donnees()
    return jsonify(donnees['mots'])

@app.route('/statistiques')
async def statistiques():
    """Page de statistiques"""
    donnees = await charger_donnees()
    mots = donnees['mots']
    
    stats = {
        'total_mots': len(mots),
        'categories': {},
        'contributeurs': {}
    }
    
    # Compter par catégorie
    for mot in mots:
        categorie = mot['categorie_grammaticale'] or 'Non spécifiée'
        stats['categories'][categorie] = stats['categories'].get(categorie, 0) + 1
        
        # Compter par contributeur
        contributeur = mot['verifie_par']
        stats['contributeurs'][contributeur] = stats['contributeurs'].get(contributeur, 0) + 1
    
    return render_template('statistiques.html', 
                         stats=stats, 
                         mots=mots)

@app.route('/rechercher')
async def rechercher():
    """Page de recherche"""
    terme = request.args.get('q', '')
    donnees = await charger_donnees()
    
    if terme:
        mots_trouves = [
            mot for mot in donnees['mots']
            if terme.lower() in mot['mot_kabye'].lower() 
            or terme.lower() in mot['traduction_francaise'].lower()
        ]
    else:
        mots_trouves = []
    
    return render_template('rechercher.html', 
                         mots=mots_trouves, 
                         terme=terme,
                         total=len(mots_trouves))

@app.route('/export')
async def exporter_donnees():
    """Exporter les données en JSON"""
    donnees = await charger_donnees()
    return jsonify({
        'success': True,
        'data': donnees,
        'total_mots': len(donnees['mots'])
    })

# Pas besoin d'initialisation au démarrage avec Vercel KV
# Les données sont chargées à la demande

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)