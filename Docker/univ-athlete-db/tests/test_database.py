import unittest
import sys
import os

# srcディレクトリをPythonのパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.database.db import Database
from src.database.models import Athlete, Event

class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = Database()
        cls.db.connect(':memory:')  # テスト用インメモリDB
        cls.db.create_tables()

    def test_insert_athlete(self):
        athlete = Athlete(name='John Doe', university='Sample University')
        self.db.insert_athlete(athlete)
        result = self.db.get_athlete_by_name('John Doe')
        self.assertEqual(result.name, 'John Doe')
        self.assertEqual(result.university, 'Sample University')

    def test_insert_event(self):
        athlete = Athlete(name='Jane Doe', university='Sample University')
        self.db.insert_athlete(athlete)
        event = Event(athlete_id=athlete.id, event_name='100m', record='10.5s')
        self.db.insert_event(event)
        result = self.db.get_event_by_athlete(athlete.id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].event_name, '100m')
        self.assertEqual(result[0].record, '10.5s')

    def test_get_athletes(self):
        athletes = self.db.get_all_athletes()
        self.assertGreater(len(athletes), 0)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

if __name__ == '__main__':
    unittest.main()