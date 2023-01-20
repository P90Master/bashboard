from copy import copy
from re import match

from bashboard.models import Thread
from bashboard import db
from sqlalchemy_utils import Ltree


class PathThreadTools:
    def path_to_ltree(self, path):
        thread_path = '.'.join(path)
        if thread_path.startswith('.'):
            thread_path = thread_path[1:]

        thread_path = 'main.' + thread_path if thread_path else 'main' + thread_path
        if thread_path[-1] == '.':
            thread_path = thread_path[:-1]
    
        return Ltree(thread_path)

    def is_thread_exist(self, path):
        thread_path = self.path_to_ltree(path)

        thread_existence = db.session.query(
            db.exists().where(Thread.path==thread_path)
        ).scalar()

        if thread_existence:
            return True
        
        return False

    def thread_finder(self, path):
        thread_path = self.path_to_ltree(path)

        thread = db.one_or_404(
            db.select(Thread).filter_by(path=thread_path)
        )

        return thread

    def path_handler(self, new_path, current_path=[]):
        new_path_list = new_path.split('/')
        if new_path_list and new_path_list[0]:
            while not new_path_list[-1]:
                # убираем лишние / в конце
                new_path_list.pop()

            handled_path = copy(current_path)
        else:
            handled_path = []

        new_path_list = new_path_list[::-1] 

        while new_path_list:
            node = new_path_list.pop()
            if node == '.':
                continue
            elif node == '..':
                handled_path = handled_path[:-1]
            else:
                handled_path.append(node)

        return handled_path

    def is_path_correct(self, path):
        for node in path:
            if not match("^[a-z0-9_]*$", node):
                return False
            
        return True

    def path_to_str(self, path):
        if path:
            if path[0]:
                return '/' + '-'.join(path)
        
            return '/' + '-'.join(path[1:])
        
        return '/'

    def ltree_to_readable_str(self, path):
        path_list = str(path).split('.')[1:]
        path_str = '~/' + '/'.join(path_list)       
        return path_str
