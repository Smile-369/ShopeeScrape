# 🛍️ Shopee Scraper Tool

A simple tool to collect product information and reviews from Shopee Philippines. Perfect for market research, competitor analysis, and product monitoring.

## 📋 What Does This Tool Do?

This tool helps you:
- **Search Products**: Find products by keyword and save their details
- **Scrape Shops**: Get all products from a specific shop
- **Collect Reviews**: Gather customer reviews for products
- **Analyze Reviews**: Get insights and sentiment analysis from reviews

## 🎯 Who Is This For?

- Online sellers researching products
- Market researchers
- Business owners analyzing competitors
- Anyone needing Shopee product data

## 💻 Requirements

Before you start, you need:
- A computer (Windows or Mac)
- Internet connection
- Chrome browser installed
- A Shopee Philippines account

---

## 🪟 Installation for Windows

### Step 1: Install Python

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click the big yellow button "Download Python 3.12.x"
3. Run the downloaded file
4. ⚠️ **IMPORTANT**: Check the box that says "Add Python to PATH"
5. Click "Install Now"
6. Wait for installation to complete
7. Click "Close"

**Verify Python is installed:**
1. Press `Windows Key + R`
2. Type `cmd` and press Enter
3. Type `python --version` and press Enter
4. You should see something like "Python 3.12.x"

### Step 2: Install Google Chrome

1. If you don't have Chrome, download it from [google.com/chrome](https://www.google.com/chrome/)
2. Install Chrome normally

### Step 3: Download This Tool

1. Download all the project files to a folder (e.g., `C:\ShopeeScaper`)
2. You should have these files:
   - `app.py`
   - `ShopeeTool.py`
   - `App.js`
   - `requirements.txt` (if provided)

### Step 4: Install Required Libraries

1. Press `Windows Key + R`
2. Type `cmd` and press Enter
3. Navigate to your project folder:
   ```
   cd C:\ShopeeScraper
   ```
4. Install the required libraries:
   ```
   pip install flask flask-cors undetected-chromedriver pandas textblob werkzeug
   ```
5. Wait for installation to complete (this may take a few minutes)

### Step 5: Run the Tool

1. In the same command prompt, type:
   ```
   python app.py
   ```
2. You should see messages like:
   ```
   🚀 Shopee Scraper API Server
   📡 Server starting on http://localhost:5000
   ```
3. Keep this window open while using the tool!

### Step 6: Open the Web Interface

1. Open your web browser
2. Open the `App.js` file in your browser (or create an HTML file to host it)
3. You should see the Shopee Scraper interface

---

## 🍎 Installation for Mac

### Step 1: Install Python

**Check if Python is already installed:**
1. Open Terminal (press `Cmd + Space`, type "Terminal", press Enter)
2. Type `python3 --version` and press Enter
3. If you see "Python 3.x.x", skip to Step 2
4. If not, continue below:

**Install Python:**
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.12.x for macOS
3. Open the downloaded `.pkg` file
4. Follow the installation wizard
5. Click through until installation completes

### Step 2: Install Google Chrome

1. If you don't have Chrome, download it from [google.com/chrome](https://www.google.com/chrome/)
2. Drag Chrome to your Applications folder

### Step 3: Download This Tool

1. Download all the project files to a folder (e.g., `~/ShopeScraper`)
2. You should have these files:
   - `app.py`
   - `ShopeeTool.py`
   - `App.js`

### Step 4: Install Required Libraries

1. Open Terminal (press `Cmd + Space`, type "Terminal", press Enter)
2. Navigate to your project folder:
   ```bash
   cd ~/ShopeeScraper
   ```
3. Install the required libraries:
   ```bash
   pip3 install flask flask-cors undetected-chromedriver pandas textblob werkzeug
   ```
4. Wait for installation to complete (this may take a few minutes)

### Step 5: Run the Tool

1. In the same Terminal window, type:
   ```bash
   python3 app.py
   ```
2. You should see messages like:
   ```
   🚀 Shopee Scraper API Server
   📡 Server starting on http://localhost:5000
   ```
3. Keep this Terminal window open while using the tool!

### Step 6: Open the Web Interface

1. Open your web browser
2. Open the `App.js` file in your browser (or create an HTML file to host it)
3. You should see the Shopee Scraper interface

---

## 🚀 How to Use

### First Time Setup

1. **Start the Server**: Run the Python script as shown above
2. **Initialize Browser**: Click "Initialize Browser" in the web interface
3. **Login to Shopee**: A Chrome window will open - login to your Shopee account
4. **Keep Logged In**: Don't close this Chrome window!

### Searching for Products

1. Click on "Search Products" tab
2. Enter a keyword (e.g., "laptop bag")
3. Set how many pages to scrape (1 page = ~60 products)
4. Click "Start Search"
5. Wait for completion - you'll see live progress
6. Download the CSV file when done

### Scraping a Shop

1. Click on "Shop Scraper" tab
2. Enter the Shop ID (found in the shop's URL)
3. Choose what to include:
   - Active products
   - Sold-out products
4. Click "Start Scraping"
5. Download the CSV file when done

### Collecting Reviews

1. Click on "Review Scraper" tab
2. Upload a CSV file with product links (from search or shop scraping)
3. Set maximum reviews per product
4. Click "Start Scraping"
5. Download the reviews CSV when done

### Analyzing Reviews

1. Click on "Review Analysis" tab
2. Upload a CSV file with reviews
3. Click "Start Analysis"
4. Get insights including:
   - Average ratings
   - Sentiment analysis
   - Common themes

---

## 📁 Output Files

All results are saved as CSV files in the `outputs` folder:

- **Search results**: `search_[keyword].csv`
  - Contains: Product name, price, rating, sales, link
  
- **Shop results**: `shop_[shop_id].csv`
  - Contains: All products from the shop
  
- **Reviews**: `reviews_[timestamp].csv`
  - Contains: Review text, rating, date, reviewer
  
- **Analysis**: `analysis_[timestamp].csv`
  - Contains: Sentiment scores, insights, summaries

---

## ❓ Troubleshooting

### "Python is not recognized" (Windows)
- You didn't check "Add Python to PATH" during installation
- Reinstall Python and make sure to check that box

### "Command not found: python3" (Mac)
- Python isn't installed properly
- Try using `python` instead of `python3`
- Reinstall Python from python.org

### Chrome window closes immediately
- The tool needs Chrome to stay open
- Don't close the Chrome window that opens
- If it closes, click "Initialize Browser" again

### "Driver not initialized" error
- Click the "Initialize Browser" button first
- Make sure you're logged into Shopee in the Chrome window
- Don't close the Chrome window

### Scraping stops or gets stuck
- Shopee might have rate-limited you
- Wait a few minutes and try again
- Try smaller batches (fewer pages/products)

### Can't find output files
- Check the `outputs` folder in your project directory
- On Windows: `C:\ShopeeScraper\outputs`
- On Mac: `~/ShopeeScraper/outputs`

---

## ⚠️ Important Notes

1. **Respect Shopee's Terms**: Use this tool responsibly
2. **Don't Overload**: Don't scrape too aggressively
3. **Stay Logged In**: Keep the Chrome window open while scraping
4. **Internet Required**: You need a stable internet connection
5. **Be Patient**: Large scraping jobs take time

---

## 🛑 How to Stop

1. In the web interface, you can cancel ongoing tasks
2. To completely stop the server:
   - **Windows**: Press `Ctrl + C` in the command prompt
   - **Mac**: Press `Ctrl + C` in the Terminal
3. Close all Chrome windows opened by the tool

---

## 📞 Need Help?

If you encounter issues:

1. Make sure Python is installed correctly
2. Make sure Chrome is installed
3. Check that you're logged into Shopee
4. Try restarting the server
5. Check the troubleshooting section above

---

## 📄 License & Disclaimer

This tool is for educational and research purposes. Always respect:
- Shopee's Terms of Service
- Privacy of other users
- Rate limits and fair use policies

Use at your own risk. The creators are not responsible for any misuse or violations.

---

**Version**: 1.0  
**Last Updated**: February 2026

Happy scraping! 🎉
