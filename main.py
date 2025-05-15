import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import textwrap
from dotenv import load_dotenv

# Konfigurasi
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- Fungsi Scraping Website ---
def scrape_website(url):
    """Mengambil seluruh konten text dari website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"\n🔍 Scraping: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Hapus elemen yang tidak diperlukan
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe', 'img', 'button', 'form', 'meta', 'link']):
            element.decompose()
        
        # Ekstrak teks dengan struktur
        text_content = []
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'article', 'section', 'div']):
            text = element.get_text().strip()
            if text:
                if element.name.startswith('h'):
                    text_content.append(f"\n\n**{text.upper()}**\n")
                else:
                    text_content.append(text)
        
        full_text = " ".join(text_content)
        print(f"✅ Retrieved {len(full_text)} characters")
        return full_text[:20000]  # Batasi ukuran
    
    except Exception as e:
        return f"Error: Failed to scrape website - {str(e)}"

# --- Fungsi AI Bilingual Generator ---
def generate_bilingual_content(scraped_content, product_name):
    """Membuat konten edukasi crypto bilingual"""
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        prompt = f"""
        Anda adalah ahli konten edukasi crypto. Buat Twitter thread bilingual dari konten berikut:
        
        INSTRUKSI:
        1. Buat dalam 2 versi:
           - Bahasa Indonesia (awali dengan [ID])
           - English (awali dengan [EN])
        2. Struktur masing-masing versi:
           - Tweet 1: Hook menarik
           - Tweet 2: Poin utama
           - Tweet 3: Solusi Produk
           - Tweet 4: Perbandingan
           - Tweet 5: Data
           - Tweet 6: CTA halus
           - Tweet 7: FAQ
           - Tweet 8: Kesimpulan
        3. Gunakan emoji dan bahasa natural
        4. Maksimal 8 tweet per bahasa
        
        DATA PRODUK:
        Nama: {product_name}
        Konten website: {scraped_content[:10000]}
        """
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 3000
            }
        )
        return response.text
    
    except Exception as e:
        return f"Error: Failed to generate content - {str(e)}"

# --- Fungsi Format Thread ---
def split_bilingual_content(content):
    """Memisahkan konten bilingual menjadi 2 versi"""
    id_content = []
    en_content = []
    current_lang = None
    
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('[ID]'):
            current_lang = 'id'
            line = line.replace('[ID]', '').strip()
        elif line.startswith('[EN]'):
            current_lang = 'en'
            line = line.replace('[EN]', '').strip()
        
        if current_lang == 'id' and line:
            id_content.append(line)
        elif current_lang == 'en' and line:
            en_content.append(line)
    
    return id_content, en_content

def format_thread(content, lang_prefix=""):
    """Membuat thread Twitter dari konten"""
    tweets = []
    current_tweet = ""
    
    for line in content:
        if len(current_tweet + " " + line) <= 250:
            current_tweet += " " + line if current_tweet else line
        else:
            if current_tweet:
                tweets.append(current_tweet)
            current_tweet = line
    
    if current_tweet:
        tweets.append(current_tweet)
    
    # Tambahkan penanda bahasa
    if lang_prefix and len(tweets) > 1:
        for i in range(len(tweets)):
            tweets[i] = f"{lang_prefix} {tweets[i]} ({i+1}/{len(tweets)})"
    
    return tweets

# --- Main Program ---
def main():
    print("=== Bilingual Crypto Thread Generator ===")
    print("Input URL website untuk dibuat thread edukasi bilingual\n")
    
    # Input user
    url = input("Website URL: ").strip()
    product_name = input("Product Name: ").strip()
    
    # Langkah 1: Scraping
    scraped_content = scrape_website(url)
    if scraped_content.startswith("Error"):
        print(scraped_content)
        return
    
    # Langkah 2: Generate konten bilingual
    print("\n🌐 Generating bilingual content...")
    ai_content = generate_bilingual_content(scraped_content, product_name)
    
    if ai_content.startswith("Error"):
        print(ai_content)
        return
    
    # Langkah 3: Pisahkan konten
    id_content, en_content = split_bilingual_content(ai_content)
    
    # Langkah 4: Format thread
    id_thread = format_thread(id_content, "[ID]")
    en_thread = format_thread(en_content, "[EN]")
    
    # Simpan ke file
    with open('thread_id.txt', 'w', encoding='utf-8') as f_id, \
         open('thread_en.txt', 'w', encoding='utf-8') as f_en:
        
        f_id.write("\n\n".join(id_thread))
        f_en.write("\n\n".join(en_thread))
    
    # Tampilkan preview
    print("\n=== INDONESIAN THREAD ===")
    for i, tweet in enumerate(id_thread, 1):
        print(f"\nTweet #{i}:")
        print(tweet)
    
    print("\n=== ENGLISH THREAD ===")
    for i, tweet in enumerate(en_thread, 1):
        print(f"\nTweet #{i}:")
        print(tweet)
    
    print("\n✅ Threads saved to:")
    print(f"- Bahasa Indonesia: thread_id.txt")
    print(f"- English: thread_en.txt")

if __name__ == "__main__":
    main()