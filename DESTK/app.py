from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
from datetime import datetime, timedelta
import random
import string
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configuration pour les fichiers statiques
app.config['UPLOAD_FOLDER'] = 'static/images'

# Base de données simulée
class Produit:
    def __init__(self, id, nom, description, prix, reduction, categorie, marque, poids, stock, image, date_limite, notation=4, nb_avis=25):
        self.id = id
        self.nom = nom
        self.description = description
        self.prix = prix
        self.reduction = reduction
        self.categorie = categorie
        self.marque = marque
        self.poids = poids
        self.stock = stock
        self.image = image
        self.date_limite = date_limite
        self.notation = notation
        self.nb_avis = nb_avis
        self.avis = [
            {'auteur': 'Jean D.', 'notation': 5, 'titre': 'Excellent produit', 'contenu': 'Très bon produit, je recommande !', 'date': datetime.now() - timedelta(days=2)},
            {'auteur': 'Marie L.', 'notation': 4, 'titre': 'Bon rapport qualité-prix', 'contenu': 'Produit conforme à la description, livraison rapide.', 'date': datetime.now() - timedelta(days=5)}
        ]

class Commande:
    def __init__(self, id, reference, produits, livraison, mode_paiement, total):
        self.id = id
        self.reference = reference
        self.produits = produits
        self.livraison = livraison
        self.mode_paiement = mode_paiement
        self.total = total

# Données de produits
produits_db = [
    Produit(1, "Pommes Golden", "Pommes golden bio, calibre 70-80mm", 2.50, 30, "fruits-legumes", "BioNature", 1000, 50, "pommes.jpg", datetime.now() + timedelta(days=7)),
    Produit(2, "Yaourt Nature", "Yaourt nature bio, 4 pots de 125g", 1.80, 40, "produits-laitiers", "Ferme Bio", 500, 30, "yaourt.jpg", datetime.now() + timedelta(days=3)),
    Produit(3, "Saumon Fumé", "Tranches de saumon fumé Norvège, 200g", 5.90, 25, "viandes-poissons", "Ocean's Best", 200, 20, "saumon.jpg", datetime.now() + timedelta(days=5)),
    Produit(4, "Pâtes Penne", "Pâtes italiennes de qualité supérieure, 500g", 1.20, 0, "epicerie", "Pasta Mia", 500, 100, "pates.jpg", datetime.now() + timedelta(days=365)),
    Produit(5, "Bananes", "Bananes cavendish, origine Equateur", 1.90, 20, "fruits-legumes", "TropiFruit", 1000, 40, "bananes.jpg", datetime.now() + timedelta(days=4)),
    Produit(6, "Fromage Comté", "Comté AOP 12 mois d'affinage, 250g", 4.50, 15, "produits-laitiers", "Fromagerie du Jura", 250, 15, "comte.jpg", datetime.now() + timedelta(days=10)),
    Produit(7, "Steak Haché", "Steak haché pur boeuf 15% MG, 2x125g", 3.20, 35, "viandes-poissons", "Boucherie Premium", 250, 25, "steak.jpg", datetime.now() + timedelta(days=2)),
    Produit(8, "Riz Basmati", "Riz basmati long grain, 1kg", 2.10, 10, "epicerie", "Oriental Rice", 1000, 60, "riz.jpg", datetime.now() + timedelta(days=180))
]

# Routes
@app.route('/')
def index():
    produits_vedette = random.sample(produits_db, 4)
    return render_template('index.html', produits_vedette=produits_vedette)

@app.route('/produits')
def produits():
    categorie = request.args.get('categorie', '')
    recherche = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 8
    
    # Filtrage des produits
    produits_filtres = []
    for produit in produits_db:
        if categorie and produit.categorie != categorie:
            continue
        if recherche.lower() not in produit.nom.lower():
            continue
        produits_filtres.append(produit)
    
    # Pagination
    total_produits = len(produits_filtres)
    produits_pagines = produits_filtres[(page-1)*per_page : page*per_page]
    
    # Création d'un objet pagination simulé
    class Pagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None
    
    pagination = Pagination(produits_pagines, page, per_page, total_produits)
    
    return render_template('produits.html', produits=pagination, categorie=categorie, q=recherche)

@app.route('/produit/<int:id>')
def fiche_produit(id):
    produit = next((p for p in produits_db if p.id == id), None)
    if not produit:
        flash("Produit non trouvé", "error")
        return redirect(url_for('produits'))
    
    # Produits similaires (même catégorie)
    produits_similaires = [p for p in produits_db if p.categorie == produit.categorie and p.id != produit.id][:4]
    
    return render_template('fiche_produit.html', produit=produit, produits_similaires=produits_similaires)

@app.route('/panier')
def panier():
    panier = session.get('cart', {})
    panier_items = []
    total_panier = 0
    
    for product_id, quantity in panier.items():
        produit = next((p for p in produits_db if p.id == int(product_id)), None)
        if produit:
            panier_items.append({
                'produit': produit,
                'quantite': quantity
            })
            total_panier += produit.prix * (1 - produit.reduction/100) * quantity
    
    return render_template('panier.html', panier_items=panier_items, total_panier=round(total_panier, 2))

@app.route('/ajouter-au-panier', methods=['POST'])
def ajouter_au_panier():
    data = request.get_json()
    product_id = str(data['product_id'])
    quantity = int(data['quantity'])
    
    cart = session.get('cart', {})
    cart[product_id] = cart.get(product_id, 0) + quantity
    session['cart'] = cart
    
    return jsonify({
        'success': True,
        'cart_count': len(cart)
    })

@app.route('/maj-quantite', methods=['POST'])
def maj_quantite():
    data = request.get_json()
    product_id = str(data['product_id'])
    action = data['action']
    
    cart = session.get('cart', {})
    if product_id in cart:
        if action == 'increase':
            cart[product_id] += 1
        elif action == 'decrease' and cart[product_id] > 1:
            cart[product_id] -= 1
        
        session['cart'] = cart
    
    return jsonify({'success': True})

@app.route('/supprimer-du-panier', methods=['POST'])
def supprimer_du_panier():
    data = request.get_json()
    product_id = str(data['product_id'])
    
    cart = session.get('cart', {})
    if product_id in cart:
        del cart[product_id]
        session['cart'] = cart
    
    return jsonify({
        'success': True,
        'cart_count': len(cart)
    })

@app.route('/validation')
def validation():
    panier = session.get('cart', {})
    if not panier:
        flash("Votre panier est vide", "error")
        return redirect(url_for('panier'))
    
    panier_items = []
    total_panier = 0
    
    for product_id, quantity in panier.items():
        produit = next((p for p in produits_db if p.id == int(product_id)), None)
        if produit:
            panier_items.append({
                'produit': produit,
                'quantite': quantity
            })
            total_panier += produit.prix * (1 - produit.reduction/100) * quantity
    
    return render_template('validation.html', panier_items=panier_items, total_panier=round(total_panier, 2))

@app.route('/valider-commande', methods=['POST'])
def valider_commande():
    data = request.get_json()
    
    # Vérifier que le panier n'est pas vide
    panier = session.get('cart', {})
    if not panier:
        return jsonify({'success': False, 'error': 'Panier vide'}), 400
    
    # Calculer le total
    total = 0
    produits_commande = []
    
    for product_id, quantity in panier.items():
        produit = next((p for p in produits_db if p.id == int(product_id)), None)
        if produit:
            produits_commande.append({
                'produit': produit,
                'quantite': quantity
            })
            total += produit.prix * (1 - produit.reduction/100) * quantity
    
    # Créer une commande
    commande_id = len(session.get('commandes', [])) + 1
    reference = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    commande = {
        'id': commande_id,
        'reference': reference,
        'produits': produits_commande,
        'livraison': data['livraison'],
        'mode_paiement': data['paiement'],
        'total': round(total, 2),
        'date': datetime.now()
    }
    
    # Sauvegarder la commande
    if 'commandes' not in session:
        session['commandes'] = []
    session['commandes'].append(commande)
    
    # Vider le panier
    session.pop('cart', None)
    
    # Redirection selon le mode de paiement
    if data['paiement'] == 'carte':
        return jsonify({
            'success': True,
            'redirect': url_for('paiement', commande=commande_id),
            'commande_id': commande_id
        })
    elif data['paiement'] == 'virement':
        return jsonify({
            'success': True,
            'redirect': url_for('confirmation', commande=commande_id, mode='virement'),
            'commande_id': commande_id
        })
    else:
        # Pour PayPal, on simule une redirection
        return jsonify({
            'success': True,
            'redirect': url_for('confirmation', commande=commande_id),
            'commande_id': commande_id
        })

@app.route('/paiement')
def paiement():
    commande_id = request.args.get('commande')
    if not commande_id:
        flash("Aucune commande spécifiée", "error")
        return redirect(url_for('index'))
    
    commandes = session.get('commandes', [])
    commande = next((c for c in commandes if c['id'] == int(commande_id)), None)
    
    if not commande:
        flash("Commande non trouvée", "error")
        return redirect(url_for('index'))
    
    # Créer un objet Commande pour le template
    class CommandeTemplate:
        def __init__(self, data):
            self.id = data['id']
            self.reference = data['reference']
            self.produits = data['produits']
            self.livraison = type('Livraison', (), data['livraison'])
            self.mode_paiement = data['mode_paiement']
            self.total = data['total']
    
    return render_template('paiement.html', commande=CommandeTemplate(commande))

@app.route('/process-paiement', methods=['POST'])
def process_paiement():
    data = request.get_json()
    commande_id = data['commande_id']
    
    # Ici, vous devriez normalement intégrer une API de paiement comme Stripe
    # Pour cet exemple, on simule simplement un paiement réussi
    
    commandes = session.get('commandes', [])
    commande = next((c for c in commandes if c['id'] == int(commande_id)), None)
    
    if not commande:
        return jsonify({'success': False, 'error': 'Commande non trouvée'}), 404
    
    # Marquer la commande comme payée
    commande['statut'] = 'payé'
    commande['date_paiement'] = datetime.now()
    session['commandes'] = commandes
    
    return jsonify({
        'success': True,
        'commande_id': commande_id
    })

@app.route('/confirmation')
def confirmation():
    commande_id = request.args.get('commande')
    if not commande_id:
        flash("Aucune commande spécifiée", "error")
        return redirect(url_for('index'))
    
    commandes = session.get('commandes', [])
    commande_data = next((c for c in commandes if c['id'] == int(commande_id)), None)
    
    if not commande_data:
        flash("Commande non trouvée", "error")
        return redirect(url_for('index'))
    
    # Créer un objet Commande pour le template
    class ProduitCommande:
        def __init__(self, data):
            self.produit = type('Produit', (), data['produit'])
            self.quantite = data['quantite']
    
    class CommandeTemplate:
        def __init__(self, data):
            self.id = data['id']
            self.reference = data['reference']
            self.produits = [ProduitCommande(p) for p in data['produits']]
            self.livraison = type('Livraison', (), data['livraison'])
            self.mode_paiement = request.args.get('mode', data['mode_paiement'])
            self.total = data['total']
    
    return render_template('confirmation.html', commande=CommandeTemplate(commande_data))

if __name__ == '__main__':
    app.run(debug=True)