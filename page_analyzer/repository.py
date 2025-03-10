import os
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import DictCursor
from page_analyzer.utils import get_url_params


class Url_sql:
    def __init__(self, conn=None):
        # Инициализация класса, загрузка переменных окружения.
        load_dotenv()
        self.database_url: str = os.getenv('DATABASE_URL')
        self.conn = None

    def get_connection(self):
        # Получение соединения с базой данных.
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(self.database_url)
        return self.conn

    def make_sql(self, sql: str, sitters: tuple = ()) -> list:
        # Выполнение SQL-запроса и возврат результатов.
        result = []
        with self.get_connection().cursor(cursor_factory=DictCursor) as curr:
            curr.execute(sql, sitters)
            result = curr.fetchall()
            self.conn.commit()  # Фиксируем изменения
        return result

    def add_url(self, name: str) -> int:
        # Добавление нового URL в базу данных.
        sql = "INSERT INTO urls (name) VALUES (%s) RETURNING id;"
        id = self.make_sql(sql=sql, sitters=(name,))
        return id[0][0]

    def add_check(self, url_id: int) -> int | None:
        # Добавление новой проверки для URL.
        sql = "SELECT name FROM urls WHERE id = %s"
        url = self.make_sql(sql=sql, sitters=(url_id,))
        if not url:
            return None

        data = get_url_params(url=url[0]['name'])
        if 'error' in data:
            return None

        sql = """INSERT INTO url_checks
                    (url_id, status_code, h1, title, description)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id;"""
        id = self.make_sql(
            sql=sql,
            sitters=(url_id, 200,
                     data.get('h1', ''),
                     data.get('title', ''),
                     data.get('description', ''))
        )
        return id[0][0]

    def show_urls(self) -> list:
        # Получение списка всех URL с последними проверками.
        sql = """SELECT
                urls.id as id,
                urls.name as name,
                url_checks.status_code as status_code,
                MAX(url_checks.created_at) as created_at
                FROM urls LEFT JOIN url_checks
                ON urls.id = url_checks.url_id
                GROUP BY urls.id, urls.name, url_checks.status_code
                ORDER BY MAX(url_checks.created_at) DESC NULLS LAST;"""
        return self.make_sql(sql)

    def get_url_by_id(self, id: int) -> list:
        # Получение URL по ID.
        sql = "SELECT * from urls WHERE id = %s"
        return self.make_sql(sql=sql, sitters=(id,))

    def get_url_by_name(self, name: str) -> list:
        # Получение URL по имени.
        sql = "SELECT * from urls WHERE name = %s"
        return self.make_sql(sql=sql, sitters=(name,))

    def get_checks(self, id: int) -> list:
       # Получение списка проверок для URL.
        sql = """SELECT id, status_code, h1, title, description, created_at
                 FROM url_checks WHERE url_id = %s
                 ORDER BY created_at DESC"""
        return self.make_sql(sql=sql, sitters=(id,))
