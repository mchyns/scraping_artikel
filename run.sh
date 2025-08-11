#!/bin/bash

# Script untuk menjalankan BPS News Scraper
echo "🚀 Starting BPS News Scraper..."

# Aktivasi virtual environment
source venv/bin/activate

# Menjalankan aplikasi Flask
echo "📡 Server akan berjalan di http://localhost:5000"
echo "📝 Tekan Ctrl+C untuk menghentikan server"
echo ""

python app.py
