# 🚗 Car Scraper for OpenSooq Jordan

This project is a web scraper built with Python and Selenium that collects used car listings from [OpenSooq Jordan](https://jo.opensooq.com/ar/سيارات-ومركبات/سيارات-للبيع). It extracts detailed information about each car, cleans the data, and saves it in both Arabic and English formats for further analysis.

## ✨ Features
- Scrapes car listings page by page (handles pagination automatically).
- Extracts **12 key fields**: ID, Model, Year, Condition, Fuel Type, Mileage, Seller Type, Location, Price, Insurance, Transmission, Color.
- Intelligent **fuel type detection** with priority rules (Hybrid > Diesel > Petrol > Electric).
- Smart **car model translation** using built-in dictionaries and fallback to Wikipedia search.
- Detects **installment listings** and skips them based on keywords or price thresholds (Electric < 9000 JOD, Hybrid < 6000 JOD).
- Saves two output files:
  - `cars_arabic.xlsx` – original Arabic data.
  - `jordan_cars_kaggle.csv` – English-translated version ready for Kaggle.
- Designed to run in **headless mode** (perfect for GitHub Actions or servers).

## 📦 Requirements
- Python 3.10+
- Google Chrome browser
- Required Python packages (see `requirements.txt`)

Install dependencies with:
```bash
pip install -r requirements.txt
