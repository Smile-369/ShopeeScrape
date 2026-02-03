import undetected_chromedriver as uc
import csv
import time
import os
import random
import urllib.parse
import pandas as pd
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from textblob import TextBlob
import re
from collections import Counter
import argparse

# ============================================================================
# SCRAPING FUNCTIONS
# ============================================================================

def fetch_ratings(driver, shop_id, item_id, offset=0, limit=50):
    """Fetch product ratings/reviews"""
    api_url = (
        f"https://shopee.ph/api/v2/item/get_ratings?"
        f"filter=0&flag=1&limit={limit}&offset={offset}&type=0"
        f"&exclude_filter=1&filter_size=0&fold_filter=0"
        f"&relevant_reviews=false&request_source=2"
        f"&shopid={shop_id}&itemid={item_id}"
    )

    script = """
    var callback = arguments[arguments.length - 1];
    fetch('%s')
        .then(response => response.json())
        .then(data => callback(data))
        .catch(err => callback({'error': err.message}));
    """ % api_url

    return driver.execute_async_script(script)

def fetch_search_api(driver, keyword, newest=0, limit=60):
    """Fetch items from search results"""
    encoded_keyword = urllib.parse.quote(keyword)
    api_url = (
        f"https://shopee.ph/api/v4/search/search_items?"
        f"by=relevancy&keyword={encoded_keyword}&limit={limit}"
        f"&newest={newest}&order=desc&page_type=search"
        f"&scenario=PAGE_GLOBAL_SEARCH&source=SRP&version=2"
    )

    script = """
    var callback = arguments[arguments.length - 1];
    fetch('%s')
        .then(response => response.json())
        .then(data => callback(data))
        .catch(err => callback({'error': err.message}));
    """ % api_url

    return driver.execute_async_script(script)

def fetch_shop_items_api(driver, shop_id, limit=30, offset=0):
    """Fetch active shop items"""
    api_url = (
        f"https://shopee.ph/api/v4/recommend/recommend?"
        f"bundle=shop_page_product_tab_main&limit={limit}&offset={offset}"
        f"&section=shop_page_product_tab_main_sec&shopid={shop_id}"
    )

    script = """
    var callback = arguments[arguments.length - 1];
    fetch('%s')
        .then(response => response.json())
        .then(data => callback(data))
        .catch(err => callback({'error': err.message}));
    """ % api_url

    return driver.execute_async_script(script)

def fetch_soldout_items_api(driver, shop_id, limit=30, offset=0):
    """Fetch sold-out items"""
    api_url = (
        f"https://shopee.ph/api/v4/shop/search_items?"
        f"filter_sold_out=1&item_card_use_scene=search_items_popular"
        f"&limit={limit}&offset={offset}&order=desc"
        f"&shopid={shop_id}&sort_by=pop&use_case=4"
    )

    script = """
    var callback = arguments[arguments.length - 1];
    fetch('%s')
        .then(response => response.json())
        .then(data => callback(data))
        .catch(err => callback({'error': err.message}));
    """ % api_url

    return driver.execute_async_script(script)

def clean_price(price_val):
    """Converts Shopee's 100,000-based integer to standard currency."""
    if price_val:
        return price_val / 100000
    return 0

def handle_captcha(driver, shop_id, fetch_func, **kwargs):
    """Handle captcha detection and retry"""
    response = fetch_func(driver, shop_id, **kwargs)
    
    if response.get('error') == 90309999:
        print("ALERT: Bot detection triggered!")
        print("Please go to the browser and solve any Captcha.")
        input("Press Enter once you've proven you're human...")
        response = fetch_func(driver, shop_id, **kwargs)
    
    return response

# ============================================================================
# SCRAPING MODES
# ============================================================================

def scrape_search(driver, keyword, max_pages=10, output_file=None):
    """Scrape items from search results"""
    if not output_file:
        output_file = f"search_{keyword.replace(' ', '_')}.csv"
    
    with open(output_file, "w", newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Shop ID", "Item ID", "Product Name", 
            "Price (Current)", "Discount %", 
            "Price Min", "Price Max", "Price Before Discount",
            "Stock", "Sold", "Item Status"
        ])

        newest = 0
        limit = 60
        total_items = 0
        
        print("\n" + "="*50)
        print(f"SEARCHING FOR: {keyword}")
        print("="*50)
        
        for page in range(max_pages):
            print(f"Fetching search page {page + 1}...")
            response = fetch_search_api(driver, keyword, newest=newest, limit=limit)

            if response.get('error') == 90309999:
                print("ALERT: Bot detection triggered!")
                print("Please solve the Captcha in the browser.")
                input("Press Enter after solving...")
                response = fetch_search_api(driver, keyword, newest=newest, limit=limit)
            
            if 'items' in response and response['items']:
                for item in response['items']:
                    ib = item.get('item_basic', {})
                    
                    shop_id = ib.get('shopid')
                    item_id = ib.get('itemid')
                    name = ib.get('name')
                    
                    price = clean_price(ib.get('price'))
                    discount = ib.get('raw_discount', ib.get('discount'))
                    p_min = clean_price(ib.get('price_min'))
                    p_max = clean_price(ib.get('price_max'))
                    p_before = clean_price(ib.get('price_before_discount'))
                    stock = ib.get('stock', 0)
                    sold = ib.get('historical_sold', 0)
                    item_status = ib.get('item_status', 'active')

                    writer.writerow([
                        shop_id, item_id, name, 
                        price, discount, 
                        p_min, p_max, p_before,
                        stock, sold, item_status
                    ])
                    total_items += 1
                
                newest += limit
                time.sleep(random.uniform(3, 5))
            else:
                print("No more items found.")
                break
    
    print(f"\n✅ Found {total_items} items")
    print(f"📄 Saved to: {output_file}")
    return output_file

def scrape_shop(driver, shop_id, include_active=True, include_soldout=True, output_file=None):
    """Scrape items from a specific shop"""
    if not output_file:
        output_file = f"shop_items_{shop_id}.csv"
    
    with open(output_file, "w", newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Shop ID", "Item ID", "Product Name", 
            "Price (Current)", "Discount %", 
            "Price Min", "Price Max", "Price Before Discount",
            "Stock", "Sold", "Item Status"
        ])

        total_active = 0
        total_soldout = 0

        # Fetch active items
        if include_active:
            print("\n" + "="*50)
            print("FETCHING ACTIVE ITEMS")
            print("="*50)
            
            offset = 0
            limit = 30
            
            for page in range(10):
                print(f"Fetching active page {page + 1}...")
                response = handle_captcha(driver, shop_id, fetch_shop_items_api, limit=limit, offset=offset)
                
                if 'data' in response and 'sections' in response['data']:
                    sections = response['data']['sections']
                    if sections and 'data' in sections[0] and 'item' in sections[0]['data']:
                        items = sections[0]['data']['item']
                        
                        if not items:
                            break
                        
                        for item in items:
                            writer.writerow([
                                item.get('shopid'),
                                item.get('itemid'),
                                item.get('name'),
                                clean_price(item.get('price')),
                                item.get('raw_discount'),
                                clean_price(item.get('price_min')),
                                clean_price(item.get('price_max')),
                                clean_price(item.get('price_before_discount')),
                                item.get('stock', 0),
                                item.get('historical_sold', 0),
                                'active'
                            ])
                            total_active += 1
                        
                        offset += limit
                        time.sleep(random.uniform(3, 5))
                    else:
                        break
                else:
                    break
        
        # Fetch sold-out items
        if include_soldout:
            print("\n" + "="*50)
            print("FETCHING SOLD-OUT ITEMS")
            print("="*50)
            
            offset = 0
            limit = 30
            
            for page in range(20):
                print(f"Fetching sold-out page {page + 1}...")
                response = handle_captcha(driver, shop_id, fetch_soldout_items_api, limit=limit, offset=offset)
                
                if 'items' in response:
                    items = response['items']
                    
                    if not items:
                        break
                    
                    for item in items:
                        ib = item.get('item_basic', {})
                        writer.writerow([
                            ib.get('shopid'),
                            ib.get('itemid'),
                            ib.get('name'),
                            clean_price(ib.get('price')),
                            ib.get('raw_discount'),
                            clean_price(ib.get('price_min')),
                            clean_price(ib.get('price_max')),
                            clean_price(ib.get('price_before_discount')),
                            ib.get('stock', 0),
                            ib.get('historical_sold', 0),
                            ib.get('item_status', 'sold_out')
                        ])
                        total_soldout += 1
                    
                    offset += limit
                    time.sleep(random.uniform(3, 5))
                else:
                    break
    
    print(f"\n✅ Active items: {total_active}")
    print(f"✅ Sold-out items: {total_soldout}")
    print(f"📄 Saved to: {output_file}")
    return output_file

def scrape_reviews_from_csv(driver, input_csv, output_file=None, max_reviews=1000):
    """Scrape reviews for products listed in a CSV file"""
    if not output_file:
        output_file = "master_reviews_list.csv"
    
    if not os.path.exists(input_csv):
        print(f"❌ File '{input_csv}' not found!")
        return None
    
    print("\n" + "="*50)
    print(f"SCRAPING REVIEWS FROM: {input_csv}")
    print("="*50)
    
    # Open Output CSV in 'Append' mode
    file_exists = os.path.isfile(output_file)
    with open(output_file, "a", newline='', encoding='utf-8-sig') as f_out:
        writer = csv.writer(f_out)
        if not file_exists:
            writer.writerow(["Product Name", "Username", "Rating", "Region", "Tags", "Comment"])

        # Read Input CSV
        with open(input_csv, "r", encoding='utf-8-sig') as f_in:
            reader = csv.DictReader(f_in)
            
            total_products = 0
            total_reviews = 0
            
            for row in reader:
                shop_id = row.get('Shop ID') 
                item_id = row.get('Item ID')
                product_name = row.get('Product Name')
                
                if not shop_id or not item_id:
                    print(f"Skipping row - missing Shop ID or Item ID")
                    continue
                
                total_products += 1
                print(f"\n--- Scraping Reviews for: {product_name} ---")
                
                offset = 0
                limit = 50
                item_reviews_count = 0

                # Scrape reviews for this product
                while item_reviews_count < max_reviews:
                    response = fetch_ratings(driver, shop_id, item_id, offset, limit)
                    
                    # Bot detection handling
                    if response.get('error') == 90309999:
                        print("ALERT: Bot detection triggered!")
                        print("Please go to the browser and solve any Captcha.")
                        input("Press Enter once you've proven you're human...")
                        response = fetch_ratings(driver, shop_id, item_id, offset, limit)
                    
                    if 'data' in response and response['data'].get('ratings'):
                        ratings_list = response['data']['ratings']
                        
                        if not ratings_list:
                            break  # No more reviews for this item
                        
                        for r in ratings_list:
                            username = r.get("author_username", "Anonymous")
                            star = r.get("rating_star", 0)
                            region = r.get("region", "PH")
                            tags = ", ".join(r.get("template_tags", [])) if r.get("template_tags") else ""
                            comment = r.get("comment", "").replace("\n", " ")

                            writer.writerow([product_name, username, star, region, tags, comment])

                        item_reviews_count += len(ratings_list)
                        offset += limit
                        
                        # Randomized delay
                        time.sleep(random.uniform(3, 5))
                    else:
                        if 'error' in response:
                            print(f"Error response: {response}")
                        break  # No more reviews for this item
                
                total_reviews += item_reviews_count
                print(f"✅ {product_name}: {item_reviews_count} reviews scraped")

    print(f"\n{'='*50}")
    print(f"✅ Scraping complete!")
    print(f"Products processed: {total_products}")
    print(f"Total reviews: {total_reviews}")
    print(f"📄 Saved to: {output_file}")
    print(f"{'='*50}")
    
    return output_file

# ============================================================================
# SENTIMENT ANALYSIS FUNCTIONS
# ============================================================================

def clean_text(text):
    """Clean and normalize text for analysis"""
    if pd.isna(text) or text == "":
        return ""
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+|@\w+', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_sentiment(text):
    """Get sentiment polarity using TextBlob"""
    if not text:
        return 0
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity
    except:
        return 0

def categorize_sentiment(polarity):
    """Categorize sentiment into Positive, Neutral, Negative"""
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

def calculate_consensus(ratings, sentiments):
    """Calculate consensus value (0-100)"""
    if len(ratings) == 0:
        return 0
    
    rating_std = np.std(ratings)
    rating_consensus = max(0, 100 - (rating_std * 25))
    
    sentiment_counts = Counter(sentiments)
    if sentiment_counts:
        dominant_sentiment_pct = max(sentiment_counts.values()) / len(sentiments) * 100
    else:
        dominant_sentiment_pct = 0
    
    consensus = (rating_consensus * 0.7) + (dominant_sentiment_pct * 0.3)
    return round(consensus, 2)

def generate_wordcloud(text, product_name, output_folder):
    """Generate and save wordcloud image"""
    if not text.strip():
        return None
    
    stopwords = set([
        'ang', 'ng', 'sa', 'na', 'at', 'mga', 'para', 'ko', 'mo', 'po',
        'yung', 'lang', 'naman', 'pa', 'din', 'rin', 'kasi', 'yan', 'yun',
        'the', 'and', 'is', 'it', 'to', 'of', 'a', 'in', 'for', 'on',
        'very', 'so', 'got', 'just', 'really', 'much', 'good'
    ])
    
    wordcloud = WordCloud(
        width=800, height=400,
        background_color='white',
        stopwords=stopwords,
        colormap='viridis',
        max_words=100
    ).generate(text)
    
    safe_name = re.sub(r'[^\w\s-]', '', product_name)[:50]
    filename = f"{output_folder}/{safe_name}_wordcloud.png"
    
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(f"WordCloud: {product_name[:60]}...", fontsize=12)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    return filename

def analyze_reviews(input_csv, output_csv=None):
    """Analyze reviews from CSV file"""
    with open(input_csv, 'r', encoding='utf-8-sig') as f:
        first_line = f.readline()
        delimiter = '\t' if '\t' in first_line else ','
    
    df = pd.read_csv(input_csv, sep=delimiter, encoding='utf-8-sig')
    
    print(f"Delimiter detected: '{delimiter}'")
    print(f"Columns found: {df.columns.tolist()}")
    
    if 'Product Name' not in df.columns:
        print(f"\n❌ Error: 'Product Name' column not found!")
        print(f"Available columns: {df.columns.tolist()}")
        return None
    
    output_folder = "wordclouds"
    os.makedirs(output_folder, exist_ok=True)
    
    products = df.groupby('Product Name')
    results = []
    
    for product_name, group in products:
        print(f"\n{'='*60}")
        print(f"Analyzing: {product_name}")
        print(f"{'='*60}")
        
        all_text = " ".join(
            group['Comment'].fillna('') + " " + group['Tags'].fillna('')
        )
        cleaned_text = clean_text(all_text)
        
        ratings = group['Rating'].dropna().tolist()
        avg_rating = np.mean(ratings) if ratings else 0
        
        comments = group['Comment'].fillna('').tolist()
        sentiments = []
        sentiment_scores = []
        
        for comment in comments:
            cleaned = clean_text(comment)
            score = get_sentiment(cleaned)
            sentiment_scores.append(score)
            sentiments.append(categorize_sentiment(score))
        
        avg_sentiment_score = np.mean(sentiment_scores) if sentiment_scores else 0
        consensus = calculate_consensus(ratings, sentiments)
        sentiment_dist = Counter(sentiments)
        
        wordcloud_file = generate_wordcloud(cleaned_text, product_name, output_folder)
        
        words = cleaned_text.split()
        word_freq = Counter(words)
        top_keywords = [word for word, count in word_freq.most_common(10) if len(word) > 3]
        
        results.append({
            'Product Name': product_name,
            'Total Reviews': len(group),
            'Average Rating': round(avg_rating, 2),
            'Average Sentiment Score': round(avg_sentiment_score, 3),
            'Dominant Sentiment': max(sentiment_dist, key=sentiment_dist.get) if sentiment_dist else 'N/A',
            'Positive Reviews': sentiment_dist.get('Positive', 0),
            'Neutral Reviews': sentiment_dist.get('Neutral', 0),
            'Negative Reviews': sentiment_dist.get('Negative', 0),
            'Consensus Score': consensus,
            'Top Keywords': ', '.join(top_keywords[:5]),
            'WordCloud Image': wordcloud_file
        })
        
        print(f"Total Reviews: {len(group)}")
        print(f"Average Rating: {avg_rating:.2f} ⭐")
        print(f"Sentiment Score: {avg_sentiment_score:.3f}")
        print(f"Consensus Score: {consensus:.2f}/100")
    
    results_df = pd.DataFrame(results)
    if not output_csv:
        output_csv = "product_analysis_results.csv"
    results_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    
    print(f"\n{'='*60}")
    print(f"✅ Analysis complete!")
    print(f"📊 Results saved to: {output_csv}")
    print(f"🖼️ WordClouds saved in: {output_folder}/")
    print(f"{'='*60}")
    
    return results_df

# ============================================================================
# MAIN FUNCTION WITH CLI ARGS
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Shopee Scraper & Analyzer - Scrape products and analyze reviews',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Search for products
  python script.py search --keyword "laptop" --pages 5 --output results.csv
  
  # Scrape shop items (active only)
  python script.py shop --shop-id 88069863 --active
  
  # Scrape shop items (sold-out only)
  python script.py shop --shop-id 88069863 --soldout
  
  # Scrape shop items (both)
  python script.py shop --shop-id 88069863 --active --soldout
  
  # Scrape reviews from a CSV file
  python script.py reviews --input search_laptop.csv --max-reviews 500
  
  # Analyze reviews
  python script.py analyze --input reviews.csv --output analysis.csv
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for products by keyword')
    search_parser.add_argument('--keyword', '-k', required=True, help='Search keyword')
    search_parser.add_argument('--pages', '-p', type=int, default=10, help='Number of pages to scrape (default: 10)')
    search_parser.add_argument('--output', '-o', help='Output CSV file (default: search_<keyword>.csv)')
    
    # Shop command
    shop_parser = subparsers.add_parser('shop', help='Scrape items from a shop by Shop ID')
    shop_parser.add_argument('--shop-id', '-s', required=True, help='Shop ID')
    shop_parser.add_argument('--active', action='store_true', help='Include active items')
    shop_parser.add_argument('--soldout', action='store_true', help='Include sold-out items')
    shop_parser.add_argument('--output', '-o', help='Output CSV file (default: shop_items_<shopid>.csv)')
    
    # Reviews command
    reviews_parser = subparsers.add_parser('reviews', help='Scrape reviews from products in a CSV file')
    reviews_parser.add_argument('--input', '-i', required=True, help='Input CSV file with product list (must have Shop ID, Item ID, Product Name)')
    reviews_parser.add_argument('--output', '-o', help='Output CSV file (default: master_reviews_list.csv)')
    reviews_parser.add_argument('--max-reviews', '-m', type=int, default=1000, help='Maximum reviews per product (default: 1000)')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze reviews from CSV file')
    analyze_parser.add_argument('--input', '-i', required=True, help='Input CSV file with reviews')
    analyze_parser.add_argument('--output', '-o', help='Output CSV file (default: product_analysis_results.csv)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'search':
        print("\n" + "="*60)
        print("SHOPEE SEARCH SCRAPER")
        print("="*60)
        
        options = uc.ChromeOptions()
        profile_path = os.path.join(os.getcwd(), "shopee_session")
        options.add_argument(f"--user-data-dir={profile_path}")
        driver = uc.Chrome(options=options)
        
        try:
            driver.get("https://shopee.ph/buyer/login")
            print("\n" + "="*50)
            print("LOGIN REQUIRED: Log in manually in the browser.")
            print("="*50)
            input("Press Enter AFTER logging in to start...")
            
            scrape_search(driver, args.keyword, args.pages, args.output)
            
        finally:
            driver.quit()
    
    elif args.command == 'shop':
        print("\n" + "="*60)
        print("SHOPEE SHOP SCRAPER")
        print("="*60)
        
        # Default to both if neither specified
        include_active = args.active or not args.soldout
        include_soldout = args.soldout or not args.active
        
        options = uc.ChromeOptions()
        profile_path = os.path.join(os.getcwd(), "shopee_session")
        options.add_argument(f"--user-data-dir={profile_path}")
        driver = uc.Chrome(options=options)
        
        try:
            driver.get("https://shopee.ph/buyer/login")
            print("\n" + "="*50)
            print("LOGIN REQUIRED: Log in manually in the browser.")
            print("="*50)
            input("Press Enter AFTER logging in to start...")
            
            scrape_shop(driver, args.shop_id, include_active, include_soldout, args.output)
            
        finally:
            driver.quit()
    
    elif args.command == 'reviews':
        print("\n" + "="*60)
        print("SHOPEE REVIEWS SCRAPER")
        print("="*60)
        
        options = uc.ChromeOptions()
        profile_path = os.path.join(os.getcwd(), "shopee_session")
        options.add_argument(f"--user-data-dir={profile_path}")
        driver = uc.Chrome(options=options)
        
        try:
            driver.get("https://shopee.ph/buyer/login")
            print("\n" + "="*50)
            print("LOGIN REQUIRED: Log in manually in the browser.")
            print("="*50)
            input("Press Enter AFTER logging in to start...")
            
            scrape_reviews_from_csv(driver, args.input, args.output, args.max_reviews)
            
        finally:
            driver.quit()
    
    elif args.command == 'analyze':
        print("\n" + "="*60)
        print("SHOPEE REVIEW ANALYZER")
        print("="*60)
        
        if not os.path.exists(args.input):
            print(f"❌ File '{args.input}' not found!")
            return
        
        print("\n🚀 Starting analysis...")
        try:
            results = analyze_reviews(args.input, args.output)
            
            if results is not None:
                print("\n📈 Summary Statistics:")
                print(results[['Product Name', 'Average Rating', 'Consensus Score', 'Dominant Sentiment']].to_string(index=False))
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Make sure packages are installed: pip install wordcloud textblob pandas matplotlib numpy")

if __name__ == "__main__":
    main()