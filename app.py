from flask import Flask, render_template, request, jsonify, send_file, make_response
import requests
from bs4 import BeautifulSoup
import json
import os
import csv
import io
from datetime import datetime, timedelta
from urllib.parse import urlencode
import time
import re
from urllib.parse import urlparse

app = Flask(__name__)

# Daftar topik BPS berdasarkan klasifikasi yang diberikan
BPS_TOPICS = {
    "A": {
        "name": "Pertanian, Kehutanan, dan Perikanan",
        "subcategories": {
            "1": {
                "name": "Pertanian, Peternakan, Perburuan dan Jasa Pertanian",
                "subtopics": [
                    "Tanaman Pangan",
                    "Tanaman Hortikultura Semusim", 
                    "Perkebunan Semusim",
                    "Tanaman Hortikultura Tahunan",
                    "Perkebunan Tahunan",
                    "Peternakan",
                    "Jasa Pertanian dan Perburuan"
                ]
            },
            "2": {"name": "Kehutanan dan Penebangan Kayu"},
            "3": {"name": "Perikanan"}
        }
    },
    "B": {
        "name": "Pertambangan dan Penggalian",
        "subcategories": {
            "1": {"name": "Pertambangan Minyak, Gas dan Panas Bumi"},
            "2": {"name": "Pertambangan Batubara dan Lignit"},
            "3": {"name": "Pertambangan Bijih Logam"},
            "4": {"name": "Pertambangan dan Penggalian Lainnya"}
        }
    },
    "C": {
        "name": "Industri Pengolahan",
        "subcategories": {
            "1": {
                "name": "Industri Batubara dan Pengilangan Migas",
                "subtopics": ["Industri Batu Bara", "Pengilangan Migas"]
            },
            "2": {"name": "Industri Makanan dan Minuman"},
            "3": {"name": "Pengolahan Tembakau"},
            "4": {"name": "Industri Tekstil dan Pakaian Jadi"},
            "5": {"name": "Industri Kulit, Barang dari Kulit dan Alas Kaki"},
            "6": {"name": "Industri Kayu, Barang dari Kayu dan Gabus"},
            "7": {"name": "Industri Kertas dan Barang dari Kertas"},
            "8": {"name": "Industri Kimia, Farmasi dan Obat Tradisional"},
            "9": {"name": "Industri Karet, Barang dari Karet dan Plastik"},
            "10": {"name": "Industri Barang Galian bukan Logam"},
            "11": {"name": "Industri Logam Dasar"},
            "12": {"name": "Industri Barang dari Logam, Komputer, Elektronik"},
            "13": {"name": "Industri Mesin dan Perlengkapan"},
            "14": {"name": "Industri Alat Angkutan"},
            "15": {"name": "Industri Furnitur"},
            "16": {"name": "Industri pengolahan lainnya"}
        }
    },
    "D": {
        "name": "Pengadaan Listrik dan Gas",
        "subcategories": {
            "1": {"name": "Ketenagalistrikan"},
            "2": {"name": "Pengadaan Gas dan Produksi Es"}
        }
    },
    "E": {"name": "Pengadaan Air, Pengelolaan Sampah, Limbah dan Daur Ulang"},
    "F": {"name": "Konstruksi"},
    "G": {
        "name": "Perdagangan Besar dan Eceran",
        "subcategories": {
            "1": {"name": "Perdagangan Mobil, Sepeda Motor dan Reparasinya"},
            "2": {"name": "Perdagangan Besar dan Eceran, Bukan Mobil dan Sepeda Motor"}
        }
    },
    "H": {
        "name": "Transportasi dan Pergudangan",
        "subcategories": {
            "1": {"name": "Angkutan Rel"},
            "2": {"name": "Angkutan Darat"},
            "3": {"name": "Angkutan Laut"},
            "4": {"name": "Angkutan Sungai Danau dan Penyeberangan"},
            "5": {"name": "Angkutan Udara"},
            "6": {"name": "Pergudangan dan Jasa Penunjang Angkutan"}
        }
    },
    "I": {
        "name": "Penyediaan Akomodasi dan Makan Minum",
        "subcategories": {
            "1": {"name": "Penyediaan Akomodasi"},
            "2": {"name": "Penyediaan Makan Minum"}
        }
    },
    "J": {"name": "Informasi dan Komunikasi"},
    "K": {
        "name": "Jasa Keuangan dan Asuransi",
        "subcategories": {
            "1": {"name": "Jasa Perantara Keuangan"},
            "2": {"name": "Asuransi dan Dana Pensiun"},
            "3": {"name": "Jasa Keuangan Lainnya"},
            "4": {"name": "Jasa Penunjang Keuangan"}
        }
    },
    "L": {"name": "Real Estate"},
    "M": {"name": "Jasa Perusahaan"},
    "O": {"name": "Administrasi Pemerintahan, Pertahanan dan Jaminan Sosial"},
    "P": {"name": "Jasa Pendidikan"},
    "Q": {"name": "Jasa Kesehatan dan Kegiatan Sosial"},
    "R": {"name": "Jasa lainnya"}
}

# Daerah target
TARGET_REGIONS = ["Bangkalan", "Madura", "Jawa Timur"]

class GoogleNewsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def search_news(self, query, region="", date_range=""):
        """Mencari berita di Google News"""
        search_query = f"{query}"
        if region:
            search_query += f" {region}"
        
        # Parameter untuk Google News
        params = {
            'q': search_query,
            'tbm': 'nws',  # News search
            'hl': 'id',    # Bahasa Indonesia
            'gl': 'id'     # Lokasi Indonesia
        }
        
        if date_range:
            params['tbs'] = f'cdr:1,cd_min:{date_range},cd_max:{date_range}'
            
        try:
            url = f"https://www.google.com/search?{urlencode(params)}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            news_results = []
            
            # Mencari elemen berita
            news_items = soup.find_all('div', {'class': 'SoaBEf'}) or soup.find_all('div', {'class': 'xrnccd'})
            
            for item in news_items[:10]:  # Ambil maksimal 10 berita
                try:
                    # Cari link
                    link_elem = item.find('a')
                    if not link_elem:
                        continue
                        
                    link = link_elem.get('href', '')
                    if link.startswith('/url?q='):
                        link = link.split('/url?q=')[1].split('&')[0]
                    elif link.startswith('/search'):
                        continue
                        
                    # Cari judul
                    title_elem = item.find('h3') or item.find('div', {'role': 'heading'})
                    title = title_elem.get_text(strip=True) if title_elem else 'No title'
                    
                    # Cari sumber
                    source_elem = item.find('span', {'class': 'CEMjEf'}) or item.find('cite')
                    source = source_elem.get_text(strip=True) if source_elem else 'Unknown source'
                    
                    # Cari tanggal
                    date_elem = item.find('span', {'class': 'r0bn4c'})
                    date = date_elem.get_text(strip=True) if date_elem else ''
                    
                    if link and title:
                        news_results.append({
                            'title': title,
                            'link': link,
                            'source': source,
                            'date': date,
                            'query': search_query,
                            'scraped_at': datetime.now().isoformat()
                        })
                        
                except Exception as e:
                    continue
                    
            return news_results
            
        except Exception as e:
            print(f"Error scraping: {e}")
            return []
    
    def scrape_by_topic(self, topic_code, subcategory=None, region="", date_range=""):
        """Scraping berdasarkan topik BPS"""
        results = []
        
        if topic_code not in BPS_TOPICS:
            return results
            
        topic = BPS_TOPICS[topic_code]
        
        # Jika ada subcategory
        if subcategory and 'subcategories' in topic:
            if subcategory in topic['subcategories']:
                subcat = topic['subcategories'][subcategory]
                query = subcat['name']
                
                # Jika ada subtopics
                if 'subtopics' in subcat:
                    for subtopic in subcat['subtopics']:
                        sub_results = self.search_news(subtopic, region, date_range)
                        for result in sub_results:
                            result['topic_code'] = topic_code
                            result['topic_name'] = topic['name']
                            result['subcategory'] = subtopic
                            result['region'] = region
                        results.extend(sub_results)
                        time.sleep(1)  # Delay untuk menghindari rate limit
                else:
                    sub_results = self.search_news(query, region, date_range)
                    for result in sub_results:
                        result['topic_code'] = topic_code
                        result['topic_name'] = topic['name']
                        result['subcategory'] = query
                        result['region'] = region
                    results.extend(sub_results)
        else:
            # Scraping topik utama
            query = topic['name'] if isinstance(topic, dict) and 'name' in topic else topic
            main_results = self.search_news(query, region, date_range)
            for result in main_results:
                result['topic_code'] = topic_code
                result['topic_name'] = query
                result['region'] = region
            results.extend(main_results)
            
        return results

class NewsContentScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_article_content(self, url):
        """Mengambil konten artikel dari URL"""
        try:
            # Handle demo/example URLs
            if 'example.com' in url or url.startswith('https://example.'):
                return self._get_demo_content(url)
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement', 'ads']):
                element.decompose()
            
            # Try different selectors for article content
            content_selectors = [
                'article',
                '.post-content',
                '.entry-content', 
                '.article-content',
                '.content',
                '.post-body',
                '.story-content',
                '.article-body',
                '.text-content',
                'main',
                '[role="main"]',
                '.description'
            ]
            
            content_text = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Get all paragraphs
                    paragraphs = content_elem.find_all('p')
                    if paragraphs and len(paragraphs) > 0:
                        content_text = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
                        if len(content_text) > 100:  # Only use if we got substantial content
                            break
            
            # Fallback: get all paragraphs from body
            if not content_text or len(content_text) < 100:
                paragraphs = soup.find_all('p')
                if paragraphs:
                    content_text = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
            
            # Another fallback: get text from main content areas
            if not content_text or len(content_text) < 100:
                main_content = soup.find('main') or soup.find('body')
                if main_content:
                    # Remove navigation and sidebar content
                    for unwanted in main_content.find_all(['nav', 'aside', 'header', 'footer']):
                        unwanted.decompose()
                    content_text = main_content.get_text(separator=' ', strip=True)
            
            # Clean up text
            content_text = re.sub(r'\s+', ' ', content_text).strip()
            
            # Get title
            title_elem = soup.find('title')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Get meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ""
            
            # Extract publication date
            published_date = self._extract_publication_date(soup, content_text)
            
            # If still no content, create a basic summary from title and description
            if not content_text or len(content_text) < 50:
                content_text = f"{title}. {description}" if description else f"Artikel tentang {title}"
            
            return {
                'title': title,
                'description': description,
                'content': content_text,
                'published_date': published_date,
                'url': url,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            # For demo purposes, return sample content
            if 'example.com' in url or url.startswith('https://example.'):
                return self._get_demo_content(url)
            
            return {
                'title': 'Artikel tidak dapat diakses',
                'description': '',
                'content': f'Maaf, artikel dari {url} tidak dapat diakses saat ini. Hal ini bisa terjadi karena berbagai alasan seperti: website sedang maintenance, artikel memerlukan login, atau ada pembatasan akses. Silakan coba lagi nanti atau akses artikel langsung melalui browser.',
                'published_date': 'Tidak diketahui',
                'url': url,
                'scraped_at': datetime.now().isoformat()
            }
    
    def _get_demo_content(self, url):
        """Generate demo content for example URLs"""
        demo_contents = {
            'pertanian-bangkalan': {
                'title': 'Pertanian Organik di Bangkalan Meningkat 25% dalam Satu Tahun',
                'content': 'Kabupaten Bangkalan, Madura - Sektor pertanian organik di Bangkalan mengalami peningkatan signifikan sebesar 25% dalam satu tahun terakhir. Menurut data Dinas Pertanian setempat, luas lahan pertanian organik kini mencapai 1.250 hektare dari sebelumnya 1.000 hektare. Peningkatan ini didorong oleh program pemerintah daerah yang memberikan bantuan bibit dan pelatihan kepada petani. Kepala Dinas Pertanian Bangkalan menyatakan bahwa produk organik dari Bangkalan kini mulai menembus pasar ekspor. Komoditas unggulan seperti jagung organik, kacang tanah, dan sayuran organik menjadi andalan petani lokal. Program sertifikasi organik juga telah membantu meningkatkan harga jual produk petani hingga 30% dibanding produk konvensional.'
            },
            'garam-madura': {
                'title': 'Industri Garam Madura Hadapi Tantangan Cuaca Ekstrim',
                'content': 'Pulau Madura - Industri garam tradisional di Madura menghadapi tantangan serius akibat perubahan cuaca ekstrim yang terjadi dalam beberapa bulan terakhir. Curah hujan yang tinggi dan tidak menentu telah mempengaruhi proses produksi garam rakyat. Ketua Asosiasi Petani Garam Madura menjelaskan bahwa produksi garam turun hingga 40% dibanding periode yang sama tahun lalu. Pemerintah daerah telah menyiapkan program bantuan untuk petani garam berupa perbaikan infrastruktur tambak dan teknologi pengolahan yang lebih modern. Upaya diversifikasi produk dengan mengembangkan garam beriodium dan garam industri juga sedang digalakkan untuk meningkatkan nilai ekonomis.'
            },
            'konstruksi-jatim': {
                'title': 'Sektor Konstruksi Jawa Timur Tumbuh 8,5% di Kuartal Kedua',
                'content': 'Surabaya, Jawa Timur - Sektor konstruksi di Provinsi Jawa Timur mencatat pertumbuhan positif sebesar 8,5% pada kuartal kedua tahun ini. Data dari BPS Jawa Timur menunjukkan peningkatan aktivitas konstruksi didorong oleh proyek-proyek infrastruktur strategis dan pembangunan perumahan. Mega proyek seperti pembangunan jalan tol, pelabuhan, dan bandara menjadi penggerak utama pertumbuhan sektor ini. Nilai investasi konstruksi mencapai Rp 45 triliun, meningkat dari Rp 41 triliun pada periode yang sama tahun sebelumnya. Gubernur Jawa Timur menyatakan komitmen untuk terus mengembangkan infrastruktur guna mendukung pertumbuhan ekonomi daerah dan meningkatkan daya saing regional.'
            }
        }
        
        # Determine content based on URL
        content_key = 'pertanian-bangkalan'  # default
        if 'garam' in url.lower() or 'madura' in url.lower():
            content_key = 'garam-madura'
        elif 'konstruksi' in url.lower() or 'jatim' in url.lower():
            content_key = 'konstruksi-jatim'
        elif 'pertanian' in url.lower() or 'bangkalan' in url.lower():
            content_key = 'pertanian-bangkalan'
        
        demo_content = demo_contents.get(content_key, demo_contents['pertanian-bangkalan'])
        
        # Generate demo publish dates
        demo_dates = {
            'pertanian-bangkalan': '25 Juli 2025',
            'garam-madura': '3 Agustus 2025',
            'konstruksi-jatim': '15 Juli 2025'
        }
        
        return {
            'title': demo_content['title'],
            'description': demo_content['title'],
            'content': demo_content['content'],
            'published_date': demo_dates.get(content_key, '1 Agustus 2025'),
            'url': url,
            'scraped_at': datetime.now().isoformat()
        }
    
    def _extract_publication_date(self, soup, content_text):
        """Extract publication date from article"""
        try:
            # Strategy 1: Look for JSON-LD structured data
            json_ld = soup.find('script', {'type': 'application/ld+json'})
            if json_ld:
                try:
                    data = json.loads(json_ld.string)
                    if isinstance(data, list):
                        data = data[0]
                    
                    date_published = data.get('datePublished') or data.get('dateCreated')
                    if date_published:
                        return self._format_date(date_published)
                except:
                    pass
            
            # Strategy 2: Look for meta tags
            meta_selectors = [
                ('property', 'article:published_time'),
                ('name', 'article:published_time'),
                ('property', 'article:published'),
                ('name', 'published'),
                ('name', 'date'),
                ('property', 'og:published_time'),
                ('name', 'DC.date.issued'),
                ('name', 'dcterms.created')
            ]
            
            for attr_name, attr_value in meta_selectors:
                meta_tag = soup.find('meta', {attr_name: attr_value})
                if meta_tag and meta_tag.get('content'):
                    return self._format_date(meta_tag['content'])
            
            # Strategy 3: Look for time elements
            time_elem = soup.find('time')
            if time_elem:
                datetime_attr = time_elem.get('datetime')
                if datetime_attr:
                    return self._format_date(datetime_attr)
                
                time_text = time_elem.get_text(strip=True)
                if time_text:
                    return self._parse_date_text(time_text)
            
            # Strategy 4: Look for common date patterns in content
            date_patterns = [
                r'(\d{1,2})\s+(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+(\d{4})',
                r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
                r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
            ]
            
            # Search in common date containers
            date_containers = soup.find_all(['span', 'div', 'p'], 
                                          class_=re.compile(r'date|time|publish', re.I))
            
            for container in date_containers:
                container_text = container.get_text(strip=True)
                for pattern in date_patterns:
                    match = re.search(pattern, container_text)
                    if match:
                        return self._parse_date_match(match, pattern)
            
            # Strategy 5: Search in full content
            for pattern in date_patterns:
                match = re.search(pattern, content_text)
                if match:
                    return self._parse_date_match(match, pattern)
            
            return 'Tanggal tidak diketahui'
            
        except Exception as e:
            return 'Tanggal tidak diketahui'
    
    def _format_date(self, date_str):
        """Format date string to Indonesian format"""
        try:
            # Handle ISO format
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                # Try various date formats
                formats = ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y']
                dt = None
                for fmt in formats:
                    try:
                        dt = datetime.strptime(date_str[:10], fmt)
                        break
                    except:
                        continue
                
                if not dt:
                    return date_str
            
            # Convert to Indonesian month names
            month_names = {
                1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
                5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
                9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
            }
            
            return f"{dt.day} {month_names[dt.month]} {dt.year}"
            
        except:
            return date_str
    
    def _parse_date_text(self, date_text):
        """Parse date from text"""
        # Handle relative dates
        if 'hari yang lalu' in date_text.lower():
            days_match = re.search(r'(\d+)\s*hari yang lalu', date_text.lower())
            if days_match:
                days_ago = int(days_match.group(1))
                date = datetime.now() - timedelta(days=days_ago)
                return self._format_date(date.isoformat())
        
        if 'jam yang lalu' in date_text.lower() or 'today' in date_text.lower():
            return self._format_date(datetime.now().isoformat())
        
        if 'kemarin' in date_text.lower() or 'yesterday' in date_text.lower():
            date = datetime.now() - timedelta(days=1)
            return self._format_date(date.isoformat())
        
        return date_text
    
    def _parse_date_match(self, match, pattern):
        """Parse date from regex match"""
        try:
            if 'Januari|Februari' in pattern:  # Indonesian month pattern
                day, month_name, year = match.groups()
                month_names = {
                    'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
                    'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
                    'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
                }
                month = month_names.get(month_name.lower(), 1)
                return f"{int(day)} {month_name.title()} {year}"
            
            elif pattern.count(r'\d') == 3:  # DD/MM/YYYY or YYYY/MM/DD
                if pattern.startswith(r'(\d{4})'):  # YYYY/MM/DD
                    year, month, day = match.groups()
                else:  # DD/MM/YYYY
                    day, month, year = match.groups()
                
                dt = datetime(int(year), int(month), int(day))
                return self._format_date(dt.isoformat())
            
            return str(match.group(0))
            
        except:
            return 'Tanggal tidak diketahui'
    
    def summarize_content(self, content_text, max_sentences=3):
        """Membuat ringkasan sederhana dari konten"""
        if not content_text or len(content_text.strip()) < 30:
            return "Konten artikel tidak tersedia untuk diringkas."
        
        # Handle error messages
        if 'Error mengambil konten' in content_text:
            return content_text
        
        # Clean content text
        content_text = re.sub(r'\s+', ' ', content_text).strip()
        
        # Split into sentences - improved regex
        sentences = re.split(r'[.!?]+(?=\s+[A-Z]|\s*$)', content_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 25]
        
        if not sentences:
            return "Tidak dapat membuat ringkasan dari artikel ini."
        
        if len(sentences) <= max_sentences:
            summary = '. '.join(sentences)
            if not summary.endswith('.'):
                summary += '.'
            return summary
        
        # Simple scoring: prefer sentences with important keywords
        keywords = ['ekonomi', 'bisnis', 'industri', 'perdagangan', 'pertanian', 'perikanan',
                   'konstruksi', 'transportasi', 'keuangan', 'investasi', 'produksi',
                   'penjualan', 'pasar', 'harga', 'ekspor', 'impor', 'jawa timur', 
                   'madura', 'bangkalan', 'surabaya', 'malang', 'naik', 'turun',
                   'meningkat', 'menurun', 'persen', 'miliar', 'triliun', 'rupiah']
        
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0
            sentence_lower = sentence.lower()
            
            # Score based on keywords
            for keyword in keywords:
                if keyword in sentence_lower:
                    score += 2
            
            # Prefer sentences with numbers (statistics)
            numbers = re.findall(r'\d+(?:[.,]\d+)*(?:\s*%|\s*persen|\s*miliar|\s*triliun)?', sentence)
            score += len(numbers) * 3
            
            # Prefer longer sentences (more informative)
            score += min(len(sentence) / 100, 3)
            
            # Prefer sentences at the beginning
            if i < 3:
                score += 2
            elif i < 5:
                score += 1
            
            # Bonus for sentences mentioning locations
            locations = ['bangkalan', 'madura', 'jawa timur', 'jatim', 'surabaya', 'malang']
            for location in locations:
                if location in sentence_lower:
                    score += 1
            
            scored_sentences.append((score, sentence, i))
        
        # Sort by score and take top sentences, but maintain order
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        top_sentences = scored_sentences[:max_sentences]
        
        # Sort by original position to maintain narrative flow  
        top_sentences.sort(key=lambda x: x[2])
        
        summary = '. '.join([sent[1] for sent in top_sentences])
        if not summary.endswith('.'):
            summary += '.'
            
        return summary
    
    def extract_hashtags(self, content_text, title=""):
        """Ekstrak hashtag dari konten berdasarkan kata kunci penting"""
        if not content_text:
            return []
        
        # Handle error messages
        if 'Error mengambil konten' in content_text or 'tidak dapat diakses' in content_text:
            return ['#ArtikelTidakTersedia']
        
        text_to_analyze = f"{title} {content_text}".lower()
        hashtags = []
        
        # Kategori hashtag berdasarkan BPS topics
        hashtag_mapping = {
            'pertanian': ['pertanian', 'tani', 'sawah', 'padi', 'jagung', 'kedelai', 'hortikultura', 'organik'],
            'peternakan': ['peternakan', 'sapi', 'ayam', 'kambing', 'ternak', 'susu', 'telur'],
            'perikanan': ['perikanan', 'ikan', 'laut', 'tambak', 'nelayan', 'budidaya', 'garam'],
            'pertambangan': ['pertambangan', 'tambang', 'minyak', 'gas', 'batubara', 'mineral'],
            'industri': ['industri', 'pabrik', 'manufaktur', 'produksi', 'tekstil', 'makanan'],
            'konstruksi': ['konstruksi', 'bangunan', 'infrastruktur', 'jalan', 'jembatan'],
            'perdagangan': ['perdagangan', 'dagang', 'pasar', 'toko', 'retail', 'eceran'],
            'transportasi': ['transportasi', 'angkutan', 'logistik', 'pelabuhan', 'bandara'],
            'keuangan': ['keuangan', 'bank', 'kredit', 'investasi', 'modal', 'asuransi'],
            'pariwisata': ['pariwisata', 'wisata', 'hotel', 'restoran', 'kuliner'],
            'teknologi': ['teknologi', 'digital', 'online', 'aplikasi', 'internet', 'startup'],
            'pendidikan': ['pendidikan', 'sekolah', 'universitas', 'siswa', 'mahasiswa', 'guru'],
            'kesehatan': ['kesehatan', 'rumah sakit', 'dokter', 'obat', 'vaksin', 'medis'],
            'ekspor': ['ekspor', 'export', 'luar negeri', 'internasional'],
            'impor': ['impor', 'import', 'luar negeri'],
            'investasi': ['investasi', 'investor', 'modal', 'dana'],
            'ekonomi': ['ekonomi', 'ekonomis', 'gdp', 'pdb', 'inflasi', 'deflasi'],
            'covid': ['covid', 'pandemi', 'corona', 'virus'],
            'jatim': ['jawa timur', 'jatim', 'surabaya', 'malang', 'kediri'],
            'madura': ['madura', 'pamekasan', 'sumenep', 'sampang'],
            'bangkalan': ['bangkalan']
        }
        
        # Check for regional tags
        regions = {
            'JawaTimur': ['jawa timur', 'jatim', 'east java'],
            'Madura': ['madura'],
            'Bangkalan': ['bangkalan'],
            'Surabaya': ['surabaya'],
            'Malang': ['malang']
        }
        
        for tag, keywords in regions.items():
            if any(keyword in text_to_analyze for keyword in keywords):
                hashtags.append(f"#{tag}")
        
        # Check for sector tags
        for tag, keywords in hashtag_mapping.items():
            if any(keyword in text_to_analyze for keyword in keywords):
                hashtags.append(f"#{tag.title()}")
        
        # Add economic indicators
        if any(word in text_to_analyze for word in ['naik', 'meningkat', 'tumbuh', 'positif']):
            hashtags.append("#Pertumbuhan")
        
        if any(word in text_to_analyze for word in ['turun', 'menurun', 'anjlok', 'minus']):
            hashtags.append("#Penurunan")
        
        if any(word in text_to_analyze for word in ['persen', '%', 'miliar', 'triliun', 'ribu']):
            hashtags.append("#Statistik")
        
        # Remove duplicates and limit to 8 hashtags
        hashtags = list(set(hashtags))[:8]
        
        return hashtags

def save_to_json(data, filename):
    """Menyimpan data ke file JSON"""
    os.makedirs('data', exist_ok=True)
    filepath = f'data/{filename}'
    
    # Load existing data
    existing_data = []
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            existing_data = []
    
    # Menggabungkan data baru dengan data yang ada
    existing_links = {item.get('link', '') for item in existing_data}
    new_data = [item for item in data if item.get('link', '') not in existing_links]
    
    if new_data:
        existing_data.extend(new_data)
        
        # Simpan data
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        
        return len(new_data)
    return 0

def load_from_json(filename):
    """Memuat data dari file JSON"""
    filepath = f'data/{filename}'
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

@app.route('/')
def index():
    return render_template('index.html', topics=BPS_TOPICS, regions=TARGET_REGIONS)

@app.route('/scrape', methods=['POST'])
def scrape_news():
    try:
        data = request.get_json()
        topic_code = data.get('topic_code', '')
        subcategory = data.get('subcategory', '')
        region = data.get('region', '')
        date_range = data.get('date_range', '')
        
        scraper = GoogleNewsScraper()
        results = scraper.scrape_by_topic(topic_code, subcategory, region, date_range)
        
        if results:
            # Simpan hasil scraping
            filename = f'news_data_{datetime.now().strftime("%Y%m%d")}.json'
            saved_count = save_to_json(results, filename)
            
            return jsonify({
                'status': 'success',
                'message': f'Berhasil scraping {len(results)} berita, {saved_count} data baru disimpan',
                'data': results,
                'total': len(results)
            })
        else:
            return jsonify({
                'status': 'warning',
                'message': 'Tidak ada berita ditemukan',
                'data': [],
                'total': 0
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}',
            'data': [],
            'total': 0
        })

@app.route('/data')
def get_data():
    """Mendapatkan data yang telah disimpan"""
    try:
        topic_filter = request.args.get('topic', '')
        region_filter = request.args.get('region', '')
        date_filter = request.args.get('date', '')
        
        # Load semua data
        all_files = []
        data_dir = 'data'
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith('.json') and file.startswith('news_data_'):
                    all_files.extend(load_from_json(file))
        
        # Filter data
        filtered_data = all_files
        
        if topic_filter:
            filtered_data = [item for item in filtered_data if item.get('topic_code') == topic_filter]
        
        if region_filter:
            filtered_data = [item for item in filtered_data if region_filter.lower() in item.get('region', '').lower()]
        
        if date_filter:
            filtered_data = [item for item in filtered_data if date_filter in item.get('scraped_at', '')]
        
        return jsonify({
            'status': 'success',
            'data': filtered_data,
            'total': len(filtered_data)
        })
        
    except Exception as ea:
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}',
            'data': [],
            'total': 0
        })

@app.route('/export-csv')
def export_csv():
    """Export data ke file CSV"""
    try:
        # Ambil parameter filter dari query string
        topic_filter = request.args.get('topic', '')
        region_filter = request.args.get('region', '')
        date_filter = request.args.get('date', '')
        
        # Load semua data (sama seperti endpoint /data)
        all_files = []
        data_dir = 'data'
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith('.json') and file.startswith('news_data_'):
                    all_files.extend(load_from_json(file))
        
        # Filter data
        filtered_data = all_files
        
        if topic_filter:
            filtered_data = [item for item in filtered_data if item.get('topic_code') == topic_filter]
        
        if region_filter:
            filtered_data = [item for item in filtered_data if region_filter.lower() in item.get('region', '').lower()]
        
        if date_filter:
            filtered_data = [item for item in filtered_data if date_filter in item.get('scraped_at', '')]
        
        if not filtered_data:
            return jsonify({
                'status': 'error',
                'message': 'Tidak ada data untuk diekspor'
            })
        
        # Buat CSV dalam memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header CSV
        headers = [
            'No',
            'Judul Berita',
            'Link',
            'Sumber',
            'Tanggal Publikasi Berita',
            'Kode Topik BPS',
            'Nama Topik BPS',
            'Sub Kategori',
            'Daerah',
            'Query Pencarian',
            'Tanggal Scraping'
        ]
        writer.writerow(headers)
        
        # Data rows
        for i, item in enumerate(filtered_data, 1):
            # Format waktu scraping
            scraped_time = item.get('scraped_at', '')
            if scraped_time:
                try:
                    dt = datetime.fromisoformat(scraped_time.replace('Z', '+00:00'))
                    scraped_time = dt.strftime('%d/%m/%Y %H:%M:%S')
                except:
                    pass
            
            row = [
                i,
                item.get('title', ''),
                item.get('link', ''),
                item.get('source', ''),
                item.get('date', ''),
                item.get('topic_code', ''),
                item.get('topic_name', ''),
                item.get('subcategory', ''),
                item.get('region', ''),
                item.get('query', ''),
                scraped_time
            ]
            writer.writerow(row)
        
        # Siapkan response
        output.seek(0)
        
        # Nama file berdasarkan filter dan tanggal
        filename_parts = ['bps_news_data']
        if topic_filter:
            filename_parts.append(f'topic_{topic_filter}')
        if region_filter:
            filename_parts.append(f'region_{region_filter}')
        if date_filter:
            filename_parts.append(f'date_{date_filter}')
        
        filename_parts.append(datetime.now().strftime('%Y%m%d_%H%M%S'))
        filename = '_'.join(filename_parts) + '.csv'
        
        # Buat response dengan file CSV
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Gagal mengekspor data: {str(e)}'
        })

@app.route('/data-manager')
def data_manager():
    """Halaman untuk mengelola data yang sudah disimpan"""
    try:
        # Hitung statistik data
        all_files = []
        data_dir = 'data'
        file_stats = []
        
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith('.json') and file.startswith('news_data_'):
                    file_path = os.path.join(data_dir, file)
                    file_data = load_from_json(file)
                    file_size = os.path.getsize(file_path)
                    
                    # Extract tanggal dari nama file
                    date_str = file.replace('news_data_', '').replace('.json', '')
                    try:
                        file_date = datetime.strptime(date_str, '%Y%m%d').strftime('%d %B %Y')
                    except:
                        file_date = date_str
                    
                    file_stats.append({
                        'filename': file,
                        'date': file_date,
                        'count': len(file_data),
                        'size': f"{file_size/1024:.1f} KB"
                    })
                    
                    all_files.extend(file_data)
        
        # Statistik umum
        total_articles = len(all_files)
        
        # Statistik per topik
        topic_stats = {}
        region_stats = {}
        source_stats = {}
        
        for item in all_files:
            # Statistik topik
            topic_code = item.get('topic_code', 'Unknown')
            topic_name = item.get('topic_name', 'Unknown')
            topic_key = f"{topic_code} - {topic_name}"
            topic_stats[topic_key] = topic_stats.get(topic_key, 0) + 1
            
            # Statistik region
            region = item.get('region', 'Unknown')
            region_stats[region] = region_stats.get(region, 0) + 1
            
            # Statistik sumber
            source = item.get('source', 'Unknown')
            source_stats[source] = source_stats.get(source, 0) + 1
        
        # Sort statistik
        topic_stats = dict(sorted(topic_stats.items(), key=lambda x: x[1], reverse=True))
        region_stats = dict(sorted(region_stats.items(), key=lambda x: x[1], reverse=True))
        source_stats = dict(sorted(source_stats.items(), key=lambda x: x[1], reverse=True)[:10])  # Top 10 sources
        
        return render_template('data_manager.html', 
                             topics=BPS_TOPICS,
                             regions=TARGET_REGIONS,
                             file_stats=file_stats,
                             total_articles=total_articles,
                             topic_stats=topic_stats,
                             region_stats=region_stats,
                             source_stats=source_stats)
        
    except Exception as e:
        return render_template('data_manager.html', 
                             topics=BPS_TOPICS,
                             regions=TARGET_REGIONS,
                             error=str(e))

@app.route('/api/delete-file/<filename>')
def delete_file(filename):
    """Menghapus file data"""
    try:
        if not filename.endswith('.json') or not filename.startswith('news_data_'):
            return jsonify({
                'status': 'error',
                'message': 'Nama file tidak valid'
            })
        
        file_path = os.path.join('data', filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({
                'status': 'success',
                'message': f'File {filename} berhasil dihapus'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'File tidak ditemukan'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Gagal menghapus file: {str(e)}'
        })

@app.route('/summarize', methods=['POST'])
def summarize_article():
    """Endpoint untuk mendapatkan ringkasan artikel"""
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        if not url:
            return jsonify({
                'status': 'error',
                'message': 'URL tidak boleh kosong',
                'summary': '',
                'hashtags': []
            })
        
        # Validate URL
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return jsonify({
                    'status': 'error',
                    'message': 'URL tidak valid',
                    'summary': '',
                    'hashtags': []
                })
        except:
            return jsonify({
                'status': 'error',
                'message': 'URL tidak valid',
                'summary': '',
                'hashtags': []
            })
        
        # Scrape content
        scraper = NewsContentScraper()
        content_data = scraper.get_article_content(url)
        
        if 'Error' in content_data['content']:
            return jsonify({
                'status': 'error',
                'message': 'Gagal mengambil konten artikel',
                'summary': content_data['content'],
                'published_date': content_data.get('published_date', 'Tanggal tidak diketahui'),
                'hashtags': []
            })
        
        # Generate summary
        summary = scraper.summarize_content(content_data['content'])
        
        # Extract hashtags
        hashtags = scraper.extract_hashtags(content_data['content'], content_data['title'])
        
        return jsonify({
            'status': 'success',
            'message': 'Berhasil membuat ringkasan',
            'title': content_data['title'],
            'summary': summary,
            'hashtags': hashtags,
            'published_date': content_data.get('published_date', 'Tanggal tidak diketahui'),
            'url': url,
            'content_length': len(content_data['content'])
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Terjadi kesalahan: {str(e)}',
            'summary': '',
            'published_date': 'Tanggal tidak diketahui',
            'hashtags': []
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)