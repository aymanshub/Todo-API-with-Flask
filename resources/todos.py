import datetime
from flask import Blueprint, url_for, abort

from flask_restful import Resource, Api, inputs, fields, \
    marshal, marshal_with, reqparse

import models

# a dict for marshaling
todo_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'completed': fields.Boolean,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime,
}


def todo_or_404(todo_id):
    """Get a Todo item if exists
    Otherwise return abort with 404 status code"""
    try:
        todo = models.Todo.get(models.Todo.id == todo_id)
    except models.Todo.DoesNotExist:
        abort(404)
    else:
        return todo


class TodoList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'name',
            required=True,
            help='No todo name provided',
            location=['form', 'json']
        )
        self.reqparse.add_argument(
            'completed',
            required=True,
            help='No status of completed provided',
            location=['form', 'json'],
            type=inputs.boolean
        )
        super().__init__()

    def get(self):
        """Get all existing Todo items"""
        todos = [marshal(todo, todo_fields)
                 for todo in models.Todo.select()]
        return todos, 200, {'Location': url_for('resources.todos.todos')}

    @marshal_with(todo_fields)
    def post(self):
        """Create a new Todo"""
        args = self.reqparse.parse_args()
        try:
            todo = models.Todo.create(**args)
        except models.IntegrityError:
            return '', 400, {'Error': 'Integrity Error'}
        return todo, 201, {'Location': url_for('resources.todos.todo', id=todo.id)}

    def delete(self):
        """
        this case was implemented as a defence when the user tries
        to delete a whole collection.
        The FE side sends such request when a new task is added but not yet saved
        and before saving the user clicks on it's Delete button.
        """
        return '', 405, {'Error': 'Method is not used correctly: Item wasn\'t saved to be deleted!'}


class Todo(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'name',
            required=True,
            help='No todo name provided',
            location=['form', 'json']
        )
        self.reqparse.add_argument(
            'completed',
            required=True,
            help='No status of completed provided',
            location=['form', 'json'],
            type=inputs.boolean
        )
        super().__init__()

    @marshal_with(todo_fields)
    def get(self, id):
        """get a Todo"""
        return todo_or_404(id)

    @marshal_with(todo_fields)
    def put(self, id):
        """Update existing Todo"""
        args = self.reqparse.parse_args()
        args['updated_at'] = datetime.datetime.now()
        query = models.Todo.update(**args).where(models.Todo.id == id)
        query.execute()
        return (models.Todo.get(models.Todo.id == id), 200,
                {'Location': url_for('resources.todos.todo', id=id)})

    def delete(self, id):
        """Delete existing Todo"""
        query = models.Todo.delete().where(models.Todo.id == id)
        query.execute()
        return '', 204, {'Location': url_for('resources.todos.todo', id=id)}


# registering the blueprint with our app
todos_api = Blueprint('resources.todos', __name__)
api = Api(todos_api)
api.add_resource(
    TodoList,
    '/todos',
    endpoint='todos'
)
api.add_resource(
    Todo,
    '/todos/<int:id>',
    endpoint='todo'
)