from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_ici'

# Données factices pour les voitures
cars = [
    {
        'id': 1,
        'name': 'Porsche 911',
        'type': 'Sport',
        'seats': 2,
        'fuel': 'Essence',
        'price': 299,
        'description': 'La Porsche 911 est une voiture de sport légendaire offrant des performances exceptionnelles et un design intemporel.',
        'reviews': 128
    },
    # Ajoutez 7 autres voitures ici...
]

# Données factices pour les réservations
bookings = []

# Utilisateurs factices
users = {
    'client@example.com': {
        'password': 'password123',
        'name': 'Jean Dupont'
    }
}

@app.route('/')
def index():
    return render_template('index.html', cars=cars[:8])

@app.route('/product/<int:id>')
def product(id):
    car = next((car for car in cars if car['id'] == id), None)
    if not car:
        return redirect(url_for('index'))
    return render_template('product.html', car=car)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in users and users[email]['password'] == password:
            session['user_email'] = email
            flash('Connexion réussie!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou mot de passe incorrect', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('index'))

@app.route('/booking/<int:id>', methods=['GET', 'POST'])
def booking(id):
    if 'user_email' not in session:
        flash('Veuillez vous connecter pour effectuer une réservation', 'warning')
        return redirect(url_for('login'))
    
    car = next((car for car in cars if car['id'] == id), None)
    if not car:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Traitement de la réservation
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        pickup_location = request.form.get('pickup_location')
        
        # Calcul du prix total (simplifié)
        days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days
        total_price = car['price'] * days + 45  # + frais
        
        # Création de la réservation
        booking = {
            'id': len(bookings) + 1,
            'car': car,
            'user_email': session['user_email'],
            'start_date': start_date,
            'end_date': end_date,
            'pickup_location': pickup_location,
            'total_price': total_price,
            'status': 'confirmed'
        }
        bookings.append(booking)
        
        return redirect(url_for('confirmation', id=booking['id']))
    
    return render_template('booking.html', car=car)

@app.route('/confirmation/<int:id>')
def confirmation(id):
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    booking = next((b for b in bookings if b['id'] == id and b['user_email'] == session['user_email']), None)
    if not booking:
        return redirect(url_for('index'))
    
    return render_template('confirmation.html', booking=booking, car=booking['car'])

@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['user_email']
    current_bookings = [b for b in bookings if b['user_email'] == user_email and b['status'] == 'confirmed']
    past_bookings = [b for b in bookings if b['user_email'] == user_email and b['status'] == 'completed']
    
    current_booking = current_bookings[0] if current_bookings else None
    
    return render_template('dashboard.html', 
                         current_user=users.get(user_email, {'name': 'Utilisateur', 'email': user_email}),
                         current_booking=current_booking,
                         past_bookings=past_bookings)

if __name__ == '__main__':
    app.run(debug=True)