python
import requests
from bs4 import BeautifulSoup
import telebot
import time
from datetime import datetime
import sqlite3

# Telegram Bot Token
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
# Telegram Kanal ID'si
CHANNEL_ID = 'YOUR_CHANNEL_ID_HERE'

# Bot'u başlat
bot = telebot.TeleBot(BOT_TOKEN)

# Kandilli URL
KANDILLI_URL = "http://www.koeri.boun.edu.tr/scripts/lst0.asp"

# Veritabanı bağlantısı
def create_db():
    conn = sqlite3.connect('earthquakes.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS earthquakes
                 (date TEXT, location TEXT, magnitude REAL, depth REAL)''')
    conn.commit()
    conn.close()

# Son depremi kontrol et
def is_new_earthquake(date, location):
    conn = sqlite3.connect('earthquakes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM earthquakes WHERE date=? AND location=?", (date, location))
    result = c.fetchone()
    conn.close()
    return result is None

# Yeni depremi kaydet
def save_earthquake(date, location, magnitude, depth):
    conn = sqlite3.connect('earthquakes.db')
    c = conn.cursor()
    c.execute("INSERT INTO earthquakes VALUES (?, ?, ?, ?)", 
              (date, location, magnitude, depth))
    conn.commit()
    conn.close()

def get_earthquake_data():
    try:
        response = requests.get(KANDILLI_URL)
        soup = BeautifulSoup(response.content, 'html.parser')
        pre_data = soup.find('pre').text.split('\n')[7:]  # İlk 7 satırı atla
        
        earthquakes = []
        for line in pre_data:
            if line.strip():
                try:
                    parts = line.split()
                    date = f"{parts[0]} {parts[1]}"
                    lat = float(parts[2])
                    lon = float(parts[3])
                    depth = float(parts[4])
                    magnitude = float(parts[6])
                    location = ' '.join(parts[8:])
                    
                    earthquakes.append({
                        'date': date,
                        'location': location,
                        'magnitude': magnitude,
                        'depth': depth,
                        'coordinates': (lat, lon)
                    })
                except:
                    continue
                    
        return earthquakes
    except Exception as e:
        print(f"Hata: {e}")
        return []

def send_earthquake_notification(earthquake):
    message = f"""🚨 YENİ DEPREM BİLDİRİMİ 🚨

📍 Lokasyon: {earthquake['location']}
📊 Büyüklük: {earthquake['magnitude']}
🕳️ Derinlik: {earthquake['depth']} km
🕒 Tarih/Saat: {earthquake['date']}
🌍 Koordinatlar: {earthquake['coordinates'][0]}, {earthquake['coordinates'][1]}

#deprem #earthquake"""

    try:
        bot.send_message(CHANNEL_ID, message, parse_mode='Markdown')
    except Exception as e:
        print(f"Mesaj gönderme hatası: {e}")

def main():
    create_db()
    print("Bot başlatıldı...")
    
    while True:
        try:
            earthquakes = get_earthquake_data()
            
            for eq in earthquakes[:5]:  # Son 5 depremi kontrol et
                if is_new_earthquake(eq['date'], eq['location']):
                    if eq['magnitude'] >= 2.0:  # Sadece 3.0 ve üzeri depremleri gönder
                        send_earthquake_notification(eq)
                        save_earthquake(eq['date'], eq['location'], 
                                     eq['magnitude'], eq['depth'])
            
            # 5 dakika bekle
            time.sleep(30)
            
        except Exception as e:
            print(f"Ana döngüde hata: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
