from flask import Flask, render_template_string, request, redirect, session, url_for
import firebase_admin
from firebase_admin import credentials, firestore
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change in production

# ---- FIREBASE SETUP ----
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

ADMIN_EMAIL = "shourikbanerjee@gmail.com"

# Get your Firebase Web API Key from Project Settings → General → Web API Key
API_KEY = "AIzaSyDPeBPAtFBDoMxTMdxadn0Y5DgZwtU5HUk"

# ---- HTML Templates ----
login_template = """
<!doctype html>
<title>Login</title>
<h2>Login</h2>
<form method="post">
  Email: <input type="email" name="email" required><br>
  Password: <input type="password" name="password" required><br>
  <button type="submit">Login</button>
</form>
"""

home_template = """
<!doctype html>
<title>Bidding</title>
<h2>Welcome {{ user_email }}</h2>
<a href="{{ url_for('logout') }}">Logout</a>
<hr>

<h3>Enter Your Bid</h3>
<form method="post" action="{{ url_for('add_bid') }}">
  Name: <input type="text" name="name" required><br>
  College: <input type="text" name="college" required><br>
  Bid Number: <input type="number" name="bid_number" required><br>
  <button type="submit">Submit</button>
</form>

<h3>Bids</h3>
<ul>
{% for entry in entries %}
  <li>{{ entry["name"] }} ({{ entry["college"] }}) - Bid: {{ entry["bid_number"] }}</li>
{% endfor %}
</ul>

{% if is_admin %}
  <form method="post" action="{{ url_for('clear_db') }}">
    <button type="submit">Clear All Entries (Admin Only)</button>
  </form>
{% endif %}
"""

# ---- ROUTES ----
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Call Firebase REST API for password verification
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
        payload = {"email": email, "password": password, "returnSecureToken": True}
        r = requests.post(url, json=payload)
        data = r.json()

        if "error" in data:
            return f"Login failed: {data['error']['message']}"

        # Store user session
        session["user_email"] = data["email"]
        session["id_token"] = data["idToken"]
        return redirect(url_for("home"))

    return render_template_string(login_template)

@app.route("/home")
def home():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user_email = session["user_email"]
    is_admin = user_email == ADMIN_EMAIL

    if is_admin:
        docs = db.collection("bids").stream()
    else:
        docs = db.collection("bids").where("email", "==", user_email).stream()

    entries = [doc.to_dict() for doc in docs]
    return render_template_string(home_template, entries=entries, user_email=user_email, is_admin=is_admin)

@app.route("/add_bid", methods=["POST"])
def add_bid():
    if "user_email" not in session:
        return redirect(url_for("login"))

    name = request.form["name"]
    college = request.form["college"]
    bid_number = request.form["bid_number"]

    db.collection("bids").add({
        "email": session["user_email"],
        "name": name,
        "college": college,
        "bid_number": bid_number
    })
    return redirect(url_for("home"))

@app.route("/clear_db", methods=["POST"])
def clear_db():
    if "user_email" not in session or session["user_email"] != ADMIN_EMAIL:
        return "Unauthorized", 403

    docs = db.collection("bids").stream()
    for doc in docs:
        doc.reference.delete()

    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
