import os
import unittest
import models
from app import app
from peewee import *
import json

TEST_DB = SqliteDatabase('test.sqlite')


class TodoBaseTests(unittest.TestCase):
    """setup and teardown"""

    # todos to create for each test in the setup phase
    todos_amount = 2

    """ helper methods """
    def create_todos(self, amount):

        data_source = [{'name': 'new todo {low_index} of {high_index} '
                                .format(low_index=i, high_index=amount - 1),
                        'completed': [True, False][i % 2]}
                       for i in range(amount)]
        try:
            models.Todo.insert_many(data_source).execute()
        except Exception as e:
            print("Error occurred during create_todos:\n {}".format(e))

    # executed prior to each test
    def setUp(self):
        TEST_DB.connect()
        TEST_DB.create_tables([models.Todo], safe=True)
        self.app = app.test_client()
        self.create_todos(self.todos_amount)

    # executed after each test
    def tearDown(self):
        TEST_DB.drop_tables([models.Todo])
        TEST_DB.close()

    """tests"""

    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_get_all_todos(self):

        response = self.app.get('/api/v1/todos')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Location'], 'http://localhost/api/v1/todos')
        self.assertEqual(len(response.json), self.todos_amount)
        for i in range(self.todos_amount):
            self.assertIn('new todo {} of {} '.format(i, self.todos_amount - 1), response.json[i]['name'])
            self.assertEqual([True, False][i % 2], response.json[i]['completed'])

    def test_create_new_todo(self):

        todo = json.dumps({
            "name": "Submit Project of unit#10",
            "completed": True,
            "edited": True
        })
        response = self.app.post('/api/v1/todos',
                                 data=todo,
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['name'], 'Submit Project of unit#10')
        self.assertEqual(response.json['completed'], True)
        self.assertEqual(response.json['updated_at'], None)

    def test_update_existing_todo(self):
        todo = {
            "id": 1,
            "name": "undo todo test 0",
            "completed": False,
            "edited": True
        }
        response = self.app.put('/api/v1/todos/1',
                                data=todo)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Location'], 'http://localhost/api/v1/todos/1')
        self.assertEqual(response.json['name'], todo['name'])
        self.assertIsNotNone(response.json['updated_at'])

    def test_delete_existing_todo(self):
        endpoint = '/api/v1/todos/2'
        response = self.app.delete(endpoint)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.headers['Location'], 'http://localhost'+endpoint)
        response = self.app.get(endpoint)
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
