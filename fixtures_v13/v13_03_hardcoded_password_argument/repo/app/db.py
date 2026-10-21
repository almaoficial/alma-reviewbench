import psycopg2

def connect():
    return psycopg2.connect(host="db", user="app", password="s3cr3t-produccion")
