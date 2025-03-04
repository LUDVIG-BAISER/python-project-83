import os
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import DictCursor
from page_analyzer.utils import get_url_params


class Url_sql:

    def __init__(self, conn=None):
        load_dotenv()
        self.database_url = os.getenv('DATABASE_URL') + "?sslmode=require"
        if not conn:
            self.conn = psycopg2.connect(self.database_url)
        else:
            self.conn = psycopg2.connect(conn)

    def make_sql(self, sql: str, sitters: tuple = ()):
        result = []
        with self.conn.cursor(cursor_factory=DictCursor) as curr:
            curr.execute(sql, sitters)
            for item in curr:
                result.append(item)
            self.conn.commit()
        return result

    def add_url(self, name: str):
        sql = "INSERT INTO urls (name) VALUES (%s) RETURNING id;"
        id = self.make_sql(sql=sql, sitters=(name,))
        return id[0][0]

    def add_check(self, url_id):
        sql = "SELECT name FROM urls WHERE id = %s"
        url = self.make_sql(sql=sql, sitters=(url_id,))[0]
        data = get_url_params(url=url)
        if 'error' in data:
            return None
        sql = """INSERT INTO url_checks
                    (url_id, status_code, h1, title, description)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id;"""
        id = self.make_sql(
            sql=sql,
            sitters=(
                url_id, 200, data['h1'],
                data['title'], data['description']))
        return id[0][0]

    def show_urls(self):
        sql = """SELECT
                urls.id as id,
                urls.name as name,
                url_checks.status_code as status_code,
                MAX(url_checks.created_at) as created_at
                FROM urls LEFT JOIN url_checks
                ON urls.id = url_checks.url_id
                GROUP BY urls.id, urls.name, url_checks.status_code
                ORDER BY MAX(url_checks.created_at) DESC NULLS LAST;
                """
        return self.make_sql(sql)

    def get_url_by_id(self, id: int):
        sql = "SELECT * from urls WHERE id = %s"
        return self.make_sql(sql=sql, sitters=(id,))

    def get_url_by_name(self, name: str):
        sql = "SELECT * from urls WHERE name = %s"
        return self.make_sql(sql=sql, sitters=(name,))

    def get_checks(self, id: int):
        sql = """SELECT id, status_code, h1, title, description, created_at
                 FROM url_checks WHERE url_id = %s
                 ORDER BY created_at DESC"""
        return self.make_sql(sql=sql, sitters=(id,))
