from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Menggunakan list/daftar agar urutan data yang dimasukkan urut dari yang terbaru
ITEMS_DATA = [
    {
        "id": "1",
        "nama": "KTM (Kartu Tanda Mahasiswa)",
        "status": "Ditemukan",
        "lokasi_peta": "Perpustakaan Pusat Lantai 2",
        "koordinat": [-7.049, 110.439],
        "penemu": "Andi",
        "deskripsi": "Ditemukan di dekat meja komputer."
    },
    {
        "id": "2",
        "nama": "Kunci Motor Honda",
        "status": "Hilang",
        "lokasi_peta": "Parkiran Fakultas Teknik",
        "koordinat": [-7.052, 110.437],
        "penemu": "Rani",
        "deskripsi": "Gantungan kunci bentuk astronot warna biru."
    }
]

@app.route('/')
def home():
    # Menampilkan data dengan urutan terbalik (data terbaru muncul paling atas)
    return render_template('index.html', items=reversed(ITEMS_DATA))

@app.route('/item/<item_id>')
def item_detail(item_id):
    # Mencari item berdasarkan ID di dalam list
    item = next((x for x in ITEMS_DATA if x["id"] == item_id), None)
    if item:
        return render_template('detail.html', item=item)
    return "Barang tidak ditemukan", 404

@app.route('/tambah', methods=['POST'])
def tambah_barang():
    nama = request.form.get('nama')
    status = request.form.get('status')
    lokasi = request.form.get('lokasi')
    deskripsi = request.form.get('deskripsi')
    penemu = request.form.get('penemu')
    
    # Membuat ID baru otomatis berdasarkan panjang data saat ini
    new_id = str(len(ITEMS_DATA) + 1)
    
    # Koordinat default (misal sekitar wilayah kampus teknik), nanti bisa dikembangkan dengan peta input
    koordinat_default = [-7.051, 110.438] 
    
    # Gabungkan jadi object baru
    new_item = {
        "id": new_id,
        "nama": nama,
        "status": status,
        "lokasi_peta": lokasi,
        "koordinat": koordinat_default,
        "penemu": penemu,
        "deskripsi": deskripsi
    }
    
    # Masukkan ke dalam database simulasi kita
    ITEMS_DATA.append(new_item)
    
    # Setelah berhasil, kembalikan user ke halaman utama
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)