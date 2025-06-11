# Gerekli kütüphaneleri içeri aktarıyoruz
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# Flask uygulamasını başlatıyoruz
# Vercel'in anlayacağı şekilde, uygulama adı 'app' olmalı
app = Flask(__name__)
CORS(app) # CORS'u hala aktif tutuyoruz, her ihtimale karşı.

# API Anahtarını GÜVENLİ BİR ŞEKİLDE ÇEVRE DEĞİŞKENLERİNDEN alıyoruz.
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    # Bu hata Vercel loglarında görünecek ve sorunu anlamamızı sağlayacak.
    print("HATA: GEMINI_API_KEY çevre değişkeni bulunamadı!")
    # Canlı ortamda hata fırlatmak yerine, bir hata mesajı döndürebiliriz.
    # raise ValueError("GEMINI_API_KEY çevre değişkeni bulunamadı!")


@app.route('/api/search', methods=['POST'])
def search_endpoint():
    """Frontend'den gelen arama isteklerini karşılayan ana fonksiyon."""
    
    # API anahtarı yoksa hemen hata döndür
    if not API_KEY:
        return jsonify({"error": "Sunucu konfigürasyon hatası: API anahtarı eksik."}), 500

    data = request.get_json()
    if not data or 'term' not in data:
        return jsonify({"error": "Arama terimi eksik"}), 400

    term = data['term']
    
    try:
        # Gemini API URL'sini burada oluşturuyoruz.
        gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

        # 1. Adım: Resmi site URL'sini bul
        url_prompt = f"Lütfen '{term}' uygulamasının veya sitesinin resmi web sitesi URL'sini tek ve sadece URL olarak ver. Yanına başka hiçbir açıklama yazma. Sadece URL. Örnek: https://example.com"
        url = call_gemini(gemini_api_url, url_prompt)
        url = url.replace("`", "").strip()
        if not url.startswith('http'):
            raise Exception("Geçerli bir URL bulunamadı.")
        
        # 2. Adım: Kategoriyi bul
        category_details = {"film-dizi": {"title": "Film & Dizi"}, "sosyal-medya": {"title": "Sosyal Medya"},"muzik": {"title": "Müzik"},"yapay-zeka": {"title": "Yapay Zekâ & Bilgi"},"oyunlar": {"title": "Oyunlar & Platformlar"},"araclar": {"title": "Araçlar & Uygulamalar"},"egitim": {"title": "Eğitim & Bilim"},"tarayicilar": {"title": "Web Tarayıcıları"}}
        category_list = ", ".join([f"'{k}' ({v['title']})" for k, v in category_details.items()])
        category_prompt = f"Bu site ({url}) şu kategorilerden hangisine en uygun: {category_list}? Sadece tek kelime olarak kategori ID'sini döndür. Örneğin: 'sosyal-medya'. Başka hiçbir açıklama yazma."
        category_id = call_gemini(gemini_api_url, category_prompt).replace("'", "").replace('"', "").replace(".", "").strip().lower()
        if category_id not in category_details:
            category_id = 'araclar'
        
        result = {"name": term, "link": url, "categoryId": category_id, "categoryTitle": category_details[category_id]['title']}
        return jsonify(result)

    except Exception as e:
        print(f"Bir hata oluştu: {e}")
        return jsonify({"error": str(e)}), 500

def call_gemini(api_url, prompt):
    """Gemini API'sine bir istek gönderir ve metin yanıtını alır."""
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.1, "maxOutputTokens": 100}}
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"API Hatası: {response.status_code} - {response.text}")
    result = response.json()
    if 'candidates' in result and result['candidates'][0].get('content', {}).get('parts', [{}])[0].get('text'):
        return result['candidates'][0]['content']['parts'][0]['text'].strip()
    else:
        raise Exception(f"Beklenmedik API yanıtı: {result}")

