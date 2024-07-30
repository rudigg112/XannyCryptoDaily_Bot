import datetime

from config import *
import mysql.connector


class DBClient:
    def __init__(self):
        dbconfig = db_config
        self.conn = mysql.connector.connect(**dbconfig)
        self.cursor = self.conn.cursor()
        timezone_offset = +3.0
        tzinfo = datetime.timezone(datetime.timedelta(hours=timezone_offset))
        self.date_now = datetime.datetime.now(tzinfo).date()

    def exit_db(self):
        try:
            self.cursor.close()
            self.conn.close()
        except Exception as e:
            print("An error occurred while closing the database connection:", e)
        finally:
            self.conn = None

    def execute_many(self, query_execute_many, values):
        self.cursor.executemany(query_execute_many, values)
        self.conn.commit()

    def select_fetchall(self, query_select_fetchall, values=()):
        self.cursor.execute(query_select_fetchall, values)
        result = self.cursor.fetchall()
        self.conn.commit()

        return result

    def select_fetchone(self, query_select_fetchone, values=()):
        self.cursor.execute(query_select_fetchone, values)
        result = self.cursor.fetchone()
        self.conn.commit()

        return result

    def update_value_in_database(self, query_update, values=()):
        print(query_update, values)
        self.cursor.execute(query_update, values)
        self.conn.commit()

    def insert_object_in_database(self, query_insert, values=()):
        self.cursor.execute(query_insert, values)
        self.conn.commit()
        result_id = self.cursor.lastrowid
        return result_id

    def delete_object_in_database(self, query_delete, values=()):
        self.cursor.execute(query_delete, values)
        self.conn.commit()

    def check_user(self, username, telegram_id):
        _sql = 'SELECT id FROM user WHERE telegram_id = %s'
        result = self.select_fetchone(_sql, (telegram_id,))

        if result is None:
            _insert = 'INSERT INTO user (telegram_username, telegram_id) VALUES (%s, %s)'
            self.insert_object_in_database(_insert, (username, telegram_id))

    def check_subs(self, selected_app, telegram_id):
        print(selected_app, telegram_id)
        _sql = ('SELECT s.id FROM subs AS s '
                'INNER JOIN apps AS a ON a.id = s.app_obj_id '
                'WHERE s.telegram_id = %s AND a.callback_data = %s')
        result = self.select_fetchone(_sql, (telegram_id, selected_app))

        _sql_get_app_id = 'SELECT id FROM apps WHERE callback_data = %s'
        app_id_result = self.select_fetchone(_sql_get_app_id, (selected_app,))

        if result:
            if app_id_result:
                _sql_delete = 'DELETE FROM subs WHERE telegram_id = %s AND app_obj_id = %s'
                self.delete_object_in_database(_sql_delete, (telegram_id, app_id_result[0]))
                text_msg = 'Ты успешно отписался от рассылки!'
            else:
                text_msg = 'Ошибка: приложение не найдено.'
        else:
            if app_id_result:
                app_id = app_id_result[0]
                _sql_insert = 'INSERT INTO subs (telegram_id, app_obj_id) VALUES (%s, %s)'
                self.insert_object_in_database(_sql_insert, (telegram_id, app_id))
                text_msg = 'Ты успешно подписался на эту тапалку!'
            else:
                text_msg = 'Ошибка: приложение не найдено.'

        return text_msg
