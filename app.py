import os
import time
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "ketemuin_super_secret_key"
DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "items": [], "chats": {}}
    with open(DB_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {"users": {}, "items": [], "chats": {}}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

# --- PERBAIKAN FITUR LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip().lower()
        password = request.form.get('password') # Mengambil data password dari login.html
        
        if username and password:
            db = load_db()
            # Memvalidasi apakah username ada di database dan password-nya cocok
            if username in db['users'] and db['users'][username] == password:
                session['username'] = username
                return redirect(url_for('index'))
            else:
                # Mengembalikan pesan error jika tidak cocok
                return "Username atau Password salah! <a href='/login'>Kembali</a>", 401
                
    return render_template('login.html')

# --- PENAMBAHAN FITUR PENDAFTARAN AKUN BARU ---
@app.route('/daftar', methods=['GET', 'POST'])
def daftar():
    if request.method == 'POST':
        username = request.form.get('username').strip().lower()
        password = request.form.get('password') # Mengambil data password dari register.html
        
        if username and password:
            db = load_db()
            # Validasi jika username ternyata sudah pernah terdaftar
            if username in db['users']:
                return "Username sudah terdaftar! Silakan gunakan username lain. <a href='/daftar'>Kembali</a>", 400
            
            # Simpan username dan password baru ke database
            db['users'][username] = password
            save_db(db)
            
            # Setelah sukses mendaftar, langsung otomatis set session/login
            session['username'] = username
            return redirect(url_for('index'))
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/tambah', methods=['POST'])
def tambah_laporan():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    status = request.form.get('status')
    nama = request.form.get('nama')
    deskripsi = request.form.get('deskripsi')
    lokasi_peta = request.form.get('lokasi')
    lat = request.form.get('latitude')
    lon = request.form.get('longitude')
    nama_file_gambar = ""
    
    upload_folder = os.path.join('static', 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        
    file_foto = request.files.get('foto_barang_cam') or request.files.get('foto_barang')
    if file_foto and file_foto.filename != '':
        ext = os.path.splitext(file_foto.filename)[1]
        nama_file_gambar = f"img_{int(time.time())}{ext}"
        file_foto.save(os.path.join(upload_folder, nama_file_gambar))
            
    data_baru = {
        "id": int(time.time()), 
        "status": status, 
        "nama": nama, 
        "deskripsi": deskripsi,
        "lokasi_peta": lokasi_peta, 
        "lat": float(lat) if lat else -6.9667, 
        "lon": float(lon) if lon else 110.4167,
        "foto": nama_file_gambar, 
        "penemu": session['username']
    }
    
    database = load_db()
    database['items'].append(data_baru)
    save_db(database)
    return redirect(url_for('index'))

# --- PROSES HAPUS BARANG TANPA MENGHAPUS CHAT ---
@app.route('/hapus/<int:item_id>')
def hapus_laporan(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    db = load_db()
    user_sekarang = session['username']
    target_item = next((i for i in db['items'] if i['id'] == item_id), None)
    
    if target_item and target_item['penemu'] == user_sekarang:
        if target_item.get('foto'):
            jalur_foto = os.path.join('static', 'uploads', target_item['foto'])
            if os.path.exists(jalur_foto):
                try: os.remove(jalur_foto)
                except: pass
                
        db['items'] = [i for i in db['items'] if i['id'] != item_id]
        save_db(db)
        
    return redirect(url_for('index'))

# --- HALAMAN DETAIL CHAT TETAP BISA DIAKSES WALAUPUN BARANG SUDAH DIHAPUS ---
@app.route('/item/<int:item_id>')
def detail_item(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    db = load_db()
    target_item = next((i for i in db['items'] if i['id'] == item_id), None)
    chat_id = str(item_id)
    
    if not target_item:
        nama_arsip = "Barang (Sudah Selesai)"
        if chat_id in db['chats'] and "nama_barang" in db['chats'][chat_id]:
            nama_arsip = f"{db['chats'][chat_id]['nama_barang']} (Selesai)"
            
        target_item = {
            "id": item_id,
            "nama": nama_arsip,
            "status": "Selesai",
            "deskripsi": "Laporan ini telah diselesaikan dan ditutup oleh penemu/pemilik barang.",
            "lokasi_peta": "Arsip Riwayat Obrolan",
            "lat": -6.9667, "lon": 110.4167, "foto": ""
        }
        
    return render_template('detail.html', item=target_item, chat_id=chat_id, username=session['username'])

# --- INBOX TETAP MENAMPILKAN CHAT DENGAN AMAN ---
@app.route('/api/home-data')
def home_data():
    if 'username' not in session: return jsonify({"items":[], "inbox":[]})
    db = load_db()
    user = session['username']
    
    inbox_list = []
    for chat_id, data in db['chats'].items():
        item_id = int(chat_id) if chat_id.isdigit() else None
        if item_id:
            item = next((i for i in db['items'] if i['id'] == item_id), None)
            
            nama_barang_terdisplay = ""
            if item:
                nama_barang_terdisplay = item['nama']
            elif "nama_barang" in data:
                nama_barang_terdisplay = f"📦 {data['nama_barang']} (Selesai)"
            else:
                nama_barang_terdisplay = "📦 Barang Terarsipkan"

            if data.get("messages"):
                msg_terakhir = data["messages"][-1]
                inbox_list.append({
                    "chat_id": chat_id,
                    "item_id": item_id,
                    "nama_barang": nama_barang_terdisplay,
                    "pengirim_terakhir": msg_terakhir["sender"],
                    "teks_terakhir": msg_terakhir["text"],
                    "total_messages": len(data["messages"])
                })
                
    return jsonify({
        "items": sorted(db['items'], key=lambda x: x['id'], reverse=True), 
        "inbox": inbox_list,
        "current_user": user
    })

@app.route('/api/chat/<chat_id>', methods=['GET', 'POST'])
def handle_chat_api(chat_id):
    if 'username' not in session: return jsonify({"status":"unauthorized"}), 401
    db = load_db()
    user = session['username']
    
    if chat_id not in db['chats']:
        db['chats'][chat_id] = {"messages": [], "nama_barang": "Barang Kehilangan"}
        
    item_id = int(chat_id) if chat_id.isdigit() else None
    if item_id:
        item = next((i for i in db['items'] if i['id'] == item_id), None)
        if item:
            db['chats'][chat_id]['nama_barang'] = item['nama']
        
    if request.method == 'POST':
        teks = request.json.get('text', '').strip()
        if teks:
            waktu = time.strftime("%H:%M")
            db['chats'][chat_id]['messages'].append({
                "sender": user, "text": teks, "time": waktu
            })
            save_db(db)
        return jsonify({"status": "success"})
        
    return jsonify(db['chats'][chat_id])

@app.route('/api/cari-lokasi')
def cari_lokasi_api():
    q = request.args.get('q', '').strip()
    if not q: return jsonify({"status": "error"})
        
    import requests
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={requests.utils.quote(q)}&countrycodes=id&limit=1"
        response = requests.get(url, headers=headers, timeout=7)
        hasil = response.json()
        if hasil and len(hasil) > 0:
            return jsonify({
                "status": "success", "lat": float(hasil[0]['lat']), "lon": float(hasil[0]['lon']), "display_name": hasil[0]['display_name']
            })
    except: pass
    return jsonify({"status": "not_found"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)