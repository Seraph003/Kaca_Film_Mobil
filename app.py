from flask import Flask, render_template, request
import cv2
import numpy as np
import os

app = Flask(__name__)

def cek_tingkat_kegelapan(gambar, kaca_coords):
    # Fungsi untuk menghitung tingkat kegelapan dari gambar yang digunakan sebagai batas
    def hitung_batas_gelap(gambar):
        gray = cv2.cvtColor(gambar, cv2.COLOR_BGR2GRAY)
        kecerahan_rata_rata = cv2.mean(gray)[0]
        return (kecerahan_rata_rata / 255) * 100  # Skala 0-255
    
    # Konversi gambar ke dalam skala keabuan
    gray = cv2.cvtColor(gambar, cv2.COLOR_BGR2GRAY)

    # Ambil area kaca mobil dari gambar
    x1, y1, x2, y2 = kaca_coords
    kaca_gray = gray[y1:y2, x1:x2]

    # Menghitung tingkat kecerahan rata-rata
    kecerahan_rata_rata = cv2.mean(kaca_gray)[0]

    # Menghitung tingkat kegelapan sebagai persentase
    tingkat_kegelapan = (kecerahan_rata_rata / 255) * 100  # Skala 0-255

    # Baca gambar yang digunakan sebagai batas
    gambar_batas_gelap = cv2.imread('./batas_gelap.png')  # Ganti dengan nama gambar yang akan digunakan sebagai batas
    batas_gelap = hitung_batas_gelap(gambar_batas_gelap)

    # Klasifikasi kegelapan
    hasil_kegelapan = 'Cukup Terang' if tingkat_kegelapan <= batas_gelap else 'Terlalu Gelap'

    # Mengembalikan hasil klasifikasi, tingkat kegelapan, dan gambar kaca yang dipotong
    return tingkat_kegelapan, hasil_kegelapan, kaca_gray

def get_kaca_coords(lines):
    # Anggap garis-garis teratas dan terbawah adalah batas kaca mobil
    top_line = lines[0][0] if lines[0][0][1] < lines[1][0][1] else lines[1][0]
    bottom_line = lines[0][0] if lines[0][0][1] >= lines[1][0][1] else lines[1][0]

    # Koordinat kaca mobil: (x1, y1, x2, y2)
    kaca_coords = (top_line[0], top_line[1], bottom_line[2], bottom_line[3])
    return kaca_coords

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hasil', methods=['POST'])
def hasil():
    # Ambil gambar yang diunggah oleh pengguna
    file = request.files['gambar']
    file_path = 'static/uploaded_image.jpg'
    file.save(file_path)

    # Baca gambar
    gambar = cv2.imread(file_path)

    # Ubah gambar menjadi skala abu-abu
    gray = cv2.cvtColor(gambar, cv2.COLOR_BGR2GRAY)

    # Deteksi tepi menggunakan Canny Edge Detection
    edges = cv2.Canny(gray, 50, 150)

    # Deteksi garis menggunakan Hough Transform
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=100, maxLineGap=10)

    # Dapatkan koordinat kaca mobil
    kaca_coords = get_kaca_coords(lines)

    # Hitung tingkat kegelapan dan hasil klasifikasi
    tingkat_kegelapan, hasil_kegelapan, kaca_gray = cek_tingkat_kegelapan(gambar, kaca_coords)

    # Simpan gambar kaca yang dipotong
    kaca_file_path = 'static/cropped_window.jpg'
    cv2.imwrite(kaca_file_path, kaca_gray)

    return render_template('hasil.html', 
                           image_file=file_path, 
                           tingkat_kegelapan=tingkat_kegelapan, 
                           hasil_kegelapan=hasil_kegelapan,
                           kaca_image_file=kaca_file_path)

if __name__ == '__main__':
    app.run(debug=True)
