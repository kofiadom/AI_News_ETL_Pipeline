import os
from eventregistry import EventRegistry, QueryArticlesIter, QueryItems
import json
import pandas as pd
import psycopg2
import boto3
import pathlib
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to extract data
def extract_data():
    api_key = ""
    if not api_key:
        raise ValueError("No API key found in environment variables. Please set 'NEWS_API_KEY'.")

    # Initialize EventRegistry with your API key
    er = EventRegistry(apiKey=api_key)

    query = QueryArticlesIter(
        keywords=QueryItems.OR(["artificial intelligence", "machine learning", "deep learning", "natural language processing", "computer vision"]),
        lang="eng",
        dataType=["news", "blog"],  # news articles and blogs
        isDuplicateFilter="skipDuplicates"  # skip duplicate articles
    )

    # Fetch articles
    articles = []
    for article in query.execQuery(er, sortBy="date", maxItems=1000):
        articles.append(article)

    # Ensure the 'data' directory exists
    os.makedirs('data', exist_ok=True)

    # Save the articles to a JSON file
    with open('ai_news_articles.json', 'w') as file:
        json.dump(articles, file, indent=4)

    # Create a DataFrame from the fetched articles
    df = pd.DataFrame(articles)

    # Keep only the required columns
    columns_to_keep = ['uri', 'lang', 'date', 'time', 'url', 'title', 'body', 'authors', 'image']
    df = df[columns_to_keep]

    # Save the DataFrame to a CSV file
    df.to_csv('ai_news_articles.csv', index=False)

    print(f'Successfully saved {len(articles)} articles to ai_news_articles.json and ai_news_articles.csv')

    return df

# Function to load data into PostgreSQL
def load_data_to_postgres(df, table_name, conn_string):
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    # Create the table if it doesn't exist
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        uri TEXT,
        lang TEXT,
        date DATE,
        time TIME,
        url TEXT,
        title TEXT,
        body TEXT,
        authors JSONB,
        image TEXT
    );
    """)

    # Insert each record into the table
    for index, row in df.iterrows():
        cur.execute(f"""
        INSERT INTO {table_name} (uri, lang, date, time, url, title, body, authors, image)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            row['uri'], row['lang'], row['date'], row['time'], row['url'], row['title'], row['body'], 
            json.dumps(row['authors']), row['image']
        ))

    # Commit the transaction
    conn.commit()

    # Close the cursor and connection
    cur.close()
    conn.close()

    print(f'Successfully loaded data into {table_name} table')

# Extract data
df = extract_data()

# Load data into PostgreSQL
table_name = 'news_articles'
conn_string = "dbname='postgres' user='postgres' host='localhost' password='harold'"

load_data_to_postgres(df, table_name, conn_string)


def upload_file_to_s3():
    s3 = boto3.client(
        service_name="s3",
        region_name="eu-north-1",
        aws_access_key_id="",
        aws_secret_access_key=""
    )
    
    bucket_name = "ai-news-pipeline"
    object_name = "ai_news_articles.csv"
    file_name = os.path.join(pathlib.Path(__file__).parent.resolve(), "ai_news_articles_1.csv")
    
    # Check if the file exists
    if not os.path.isfile(file_name):
        logger.error(f"File not found: {file_name}")
        return

    try:
        s3.upload_file(file_name, bucket_name, object_name)
        logger.info(f"File uploaded successfully to {bucket_name}/{object_name}")
    except Exception as e:
        logger.error(f"Error uploading file: {e}")

if __name__ == "__main__":
    upload_file_to_s3()
