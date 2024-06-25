import sqlite3

class AcademicRecordsModel:
    def __init__(self):
        self.conn = sqlite3.connect('academic_records.db')
        self.cursor = self.conn.cursor()
        self.initialize_database()

    def initialize_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT,
                course TEXT,
                activity_name TEXT,
                grade TEXT,
                date_given TEXT,
                date_graded TEXT,
                comment TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT
            )
        ''')
        self.conn.commit()

    def save_record(self, student_name, course, activity_name, grade, date_given, date_graded, comment):
        self.cursor.execute('''
            INSERT INTO Records (student_name, course, activity_name, grade, date_given, date_graded, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_name, course, activity_name, grade, date_given, date_graded, comment))
        self.conn.commit()

    def get_config(self, key):
        self.cursor.execute('SELECT value FROM Config WHERE key=?', (key,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def set_config(self, key, value):
        self.cursor.execute('INSERT OR REPLACE INTO Config (key, value) VALUES (?, ?)', (key, value))
        self.conn.commit()

    def close_connection(self):
        self.conn.close()
