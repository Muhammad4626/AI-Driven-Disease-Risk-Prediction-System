import psycopg2

conn = psycopg2.connect(
    database="disease_prediction",
    user="postgres",
    password="1234",
    host="localhost",
    port="5432"
)

print("Database connected")

conn.close()