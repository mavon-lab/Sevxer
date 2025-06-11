# Gerekli kütüphaneleri içeri aktarıyoruz
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# Flask uygulamasını başlatıyoruz
app = Flask(__name__)
# Frontend'in bu sunucuyla konuşabilmesi için CORS'u aktif ediyoruz
CORS(app)

# API Anahtarını GÜVENLİ BİR ŞEKİLDE ÇEVRE DEĞİŞKENLERİNDEN (ENVIRONMENT VARIABLES) alıyoruz.
API_KEY = os.environ.get("GEMINI_API_KEY")

# Eğer API anahtarı sunucuya tanımlanmamışsa, programı hata vererek durdur.
# Bu, anahtarın yanlışlıkla unutulmasını engeller.
if not API_KEY:
    raise ValueError("GEMINI_API_KEY çevre değişkeni bulunamadı! Lütfen sunucu ayarlarınıza ekleyin.")

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

# Kategorilerin listesi (Frontend ile aynı olmalı)
CATEGORY_DETAILS = {
    "film-dizi": {"title": "Film & Dizi"},
    "sosyal-medya": {"title": "Sosyal Medya"},
    "muzik": {"title": "Müzik"},
    "yapay-zeka": {"title": "Yapay Zekâ & Bilgi"},
    "oyunlar": {"title": "Oyunlar & Platformlar"},
    "araclar": {"title": "Araçlar & Uygulamalar"},
    "egitim": {"title": "Eğitim & Bilim"},
    "tarayicilar": {"title": "Web Tarayıcıları"}
}

def call_gemini(prompt):
    """Gemini API'sine bir istek gönderir ve metin yanıtını alır."""
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": { "temperature": 0.1, "maxOutputTokens": 100 }
    }
    response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"API Hatası: {response.status_code} - {response.text}")
        raise Exception("Gemini API'sine ulaşılamadı.")
    result = response.json()
    if 'candidates' in result and result['candidates'][0].get('content', {}).get('parts', [{}])[0].get('text'):
        return result['candidates'][0]['content']['parts'][0]['text'].strip()
    else:
        print(f"Beklenmedik API yanıtı: {result}")
        raise Exception("API'den geçerli bir cevap alınamadı.")

@app.route('/search', methods=['POST'])
def search_endpoint():
    """Frontend'den gelen arama isteklerini karşılayan ana fonksiyon."""
    data = request.get_json()
    if not data or 'term' not in data:
        return jsonify({"error": "Arama terimi eksik"}), 400
    term = data['term']
    try:
        url_prompt = f"Lütfen '{term}' uygulamasının veya sitesinin resmi web sitesi URL'sini tek ve sadece URL olarak ver. Yanına başka hiçbir açıklama yazma. Sadece URL. Örnek: https://example.com"
        url = call_gemini(url_prompt).replace("`", "").strip()
        if not url.startswith('http'): raise Exception("Geçerli bir URL bulunamadı.")
        
        category_list = ", ".join([f"'{k}' ({v['title']})" for k, v in CATEGORY_DETAILS.items()])
        category_prompt = f"Bu site ({url}) şu kategorilerden hangisine en uygun: {category_list}? Sadece tek kelime olarak kategori ID'sini döndür. Örneğin: 'sosyal-medya'. Başka hiçbir açıklama yazma."
        category_id = call_gemini(category_prompt).replace("'", "").replace('"', "").replace(".", "").strip().lower()
        if category_id not in CATEGORY_DETAILS: category_id = 'araclar'
        
        result = { "name": term, "link": url, "categoryId": category_id, "categoryTitle": CATEGORY_DETAILS[category_id]['title'] }
        return jsonify(result)
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
        return jsonify({"error": str(e)}), 500

# Bu dosya doğrudan çalıştırıldığında Flask sunucusunu başlatır.
# Vercel gibi platformlar bu kısmı kullanmaz, kendi sunucularını çalıştırırlar.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


