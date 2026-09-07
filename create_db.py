import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

conn = psycopg2.connect(
    dbname='postgres',
    user='postgres',
    password='1234',
    host='localhost',
    port='5432'
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()

try:
    cursor.execute('CREATE DATABASE construction_ai')
    print("Database construction_ai created successfully")
except psycopg2.errors.DuplicateDatabase:
    print("Database construction_ai already exists")

cursor.close()
conn.close()
