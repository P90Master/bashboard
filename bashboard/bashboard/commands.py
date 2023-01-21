from re import match

from flask import url_for, redirect, session
from flask_socketio import emit

from bashboard.models import Message, Thread
from bashboard import db
from bashboard.utils import PathThreadTools


tools = PathThreadTools()


class ValidationError(Exception):
    def __init__(self, message="Wrong data"):
        self.message = message
        super(ValidationError, self).__init__(message)


class NoArguments(Exception):
    pass


class Command:
    def __init__(self, tools):
        self.tools = tools

    def execute(self, *args, **kwargs):
        raise NotImplementedError()

    def name(self):
        raise NotImplementedError()
    
    def help(self):
        raise NotImplementedError()


class NotFoundCommand(Command):
    def execute(self, *args, **kwargs):
        emit('cmd_output', {'text': ["Command doesn't exist"]})

    def name(self):
        return 'not_found'
    
    def help(self):
        return ''


class ClearOutputCommand(Command):
    def execute(self, *args, **kwargs):
        emit('cmd_output_clear', {})

    def name(self):
        return ''
    
    def help(self):
        name = self.name()
        return f'/{name}: Clear command output'


class ClearAllCommand(Command):
    def execute(self, *args, **kwargs):
        emit('clear', {})

    def name(self):
        return 'clear'
    
    def help(self):
        name = self.name()
        return f'/{name}: Clear board'


class ListCommand(Command):
    def execute(self, *args, **kwargs):
        try:
            command_blocks = kwargs.get('command_blocks')
            path = kwargs.get('path')
            thread = kwargs.get('thread')
            self.list_command(path, thread, command_blocks)
        
        except ValidationError as error:
            emit('cmd_output', {'text': [error.message]})
    
    def list_command(self, path, thread, command_blocks):
        if command_blocks:
            directory = command_blocks[0].lower()
        
            directory_list = self.tools.path_handler(directory, path)
            self.validate(directory_list)
            selected_thread = self.tools.thread_finder(directory_list)
            subthreads = selected_thread.subthreads
        else:
            subthreads = thread.subthreads

        subthreads_str = ''

        for subthread in subthreads:
            subthreads_str += subthread.name + '/ '

        emit('cmd_output', {'text': [subthreads_str]})
    
    def validate(self, directory_list):
        if self.tools.is_thread_exist(directory_list):
            return

        error = "/ls: Thread doesn't exist"
        raise ValidationError(error)

    def name(self):
        return 'ls'
    
    def help(self):
        name = self.name()
        return f'/{name} [path]: Displays a list of threads in the selected thread'


class ChangeDirectoryCommand(Command):
    def execute(self, *args, **kwargs):
        try:
            command_blocks = kwargs.get('command_blocks')
            path = kwargs.get('path')
            self.change_directory(path, command_blocks)
        
        except NoArguments:
            emit('redirect', {'path': '/'})

        except ValidationError as error:
            emit('cmd_output', {'text': [error.message]})

    def change_directory(self, path, command_blocks):
        if not command_blocks:
            raise NoArguments

        route = command_blocks.pop()
        new_path = self.tools.path_handler(route, path)
        self.validate(new_path)
        path_str = tools.path_to_str(new_path)

        emit('redirect', {'path': path_str})
    
    def validate(self, new_path):
        if self.tools.is_path_correct(new_path):
            if self.tools.is_thread_exist(new_path):
                return
            
            error = '/cd: No such thread'
            raise ValidationError(error)
        
        error = "/cd: Incorrect path"
        raise ValidationError(error)

    def name(self):
        return 'cd'
    
    def help(self):
        name = self.name()
        return f'/{name} [path]: Change thread'


class MakeDirectoryCommand(Command):
    def execute(self, *args, **kwargs):
        try:
            command_blocks = kwargs.get('command_blocks')
            path = kwargs.get('path')
            self.make_directory(path, command_blocks)

        except NoArguments:
            pass
        
        except ValidationError as error:
            emit('cmd_output', {'text': [error.message]})
    
    def make_directory(self, path, command_blocks):
        if not command_blocks:
            raise NoArguments

        directory = command_blocks[0].lower()
        if not directory:
            raise NoArguments
        
        directory_list = self.tools.path_handler(directory, path)
        parent_path = directory_list[:-1]
        dirname = directory_list[-1]

        self.validate(dirname, parent_path)

        parent_thread = self.tools.thread_finder(parent_path)
        new_thread = Thread(name=dirname, parent=parent_thread)
        db.session.add(new_thread)
        db.session.commit()
        emit('cmd_output', {'text': []})

    def validate(self, dirname, parent_path):
        if match("^[a-z0-9_]*$", dirname):
            if self.tools.is_path_correct(parent_path):
                if self.tools.is_thread_exist(parent_path):
                    if not self.tools.is_thread_exist(parent_path + [dirname]):
                        return

                    error = f"/mkdir: Thread {dirname} already exist"
                    raise ValidationError(error)

                error = "/mkdir: Path doesn't exist"
                raise ValidationError(error)
            
            error = "/mkdir: Incorrect path"
            raise ValidationError(error)

        error = f"/mkdir: Thread name {dirname} incorrect"
        raise ValidationError(error)

    def name(self):
        return 'mkdir'

    def help(self):
        name = self.name()
        return f'/{name} [path/]<new_thread_name>: Create a new thread'


class RemoveDirectoryCommand(Command):
    def execute(self, *args, **kwargs):
        try:
            command_blocks = kwargs.get('command_blocks')
            path = kwargs.get('path')
            thread = kwargs.get('thread')
            self.remove_directory(path, command_blocks, thread)

        except NoArguments:
            pass
        
        except ValidationError as error:
            emit('cmd_output', {'text': [error.message]})
    
    def remove_directory(self, path, command_blocks, thread):
        if not command_blocks:
            raise NoArguments

        directory = command_blocks[0].lower()
        if not directory:
            raise NoArguments
        
        directory_list = self.tools.path_handler(directory, path)
        self.validate(directory_list)

        selected_thread = self.tools.thread_finder(directory_list)
        db.session.delete(selected_thread)
        db.session.commit()

        if selected_thread == thread:
            new_path = path[:-1]
            path_str = tools.path_to_str(new_path)

            emit('redirect', {'path': path_str})
        else:
            emit('cmd_output', {'text': []})

    def validate(self, directory_list):
        if directory_list:
            if self.tools.is_path_correct(directory_list):
                if self.tools.is_thread_exist(directory_list):
                    thread = self.tools.thread_finder(directory_list)
                    if not thread.subthreads:
                        return

                    error = "/rmdir: Thread has nested threads"
                    raise ValidationError(error)

                error = "/rmdir: Thread doesn't exist"
                raise ValidationError(error)
            
            error = "/rmdir: Incorrect path"
            raise ValidationError(error)
        
        error = "/rmdir: You can't delete main thread"
        raise ValidationError(error)

    def name(self):
        return 'rmdir'

    def help(self):
        name = self.name()
        return f'/{name} <path_to_thread/thread>: Delete thread'


class GetCommand(Command):
    def execute(self, *args, **kwargs):
        try:
            command_blocks = kwargs.get('command_blocks')
            self.get(command_blocks)
        
        except ValidationError as error:
            emit('cmd_output', {'text': [error.message]})

    def get(self, command_blocks):
        if not command_blocks:
            error = "/get: Message id required"
            raise ValidationError(error)

        id = command_blocks[0]
        self.validate(id)

        int_id = int(id)
        message = Message.query.get(int_id)
        path = message.thread.path    
        location = self.tools.ltree_to_readable_str(path)
        message_info = f'{location} : "{message.text}"'

        emit('cmd_output', {'text': [message_info]})

    def validate(self, id):
        try:
            int_id = int(id)
            message = Message.query.get(int_id)
            if message:
                return
    
            error = f"/get: Message with id {int_id} doesn't exist"
            raise ValidationError(error)

        except ValueError:
            error = "/get: id must be an integer"
            raise ValidationError(error)

    def name(self):
        return 'get'

    def help(self):
        name = self.name()
        return f'/{name} <id>: Get message by id'


class HelpCommand(Command):
    def execute(self, *args, **kwargs):
        command_blocks = kwargs.get('command_blocks')

        if command_blocks:
            command = command_blocks[0]
            cmd_instance = COMMANDS.get(command.lower())

            if cmd_instance:
                emit('cmd_output', {'text': [cmd_instance.help()]})
            else:
                emit('cmd_output', {'text': [f"/help: command {command} doesn't exist"]})

        else:
            output = [
            'About path handling:',
            '"/" at the beginning - absolute path',
            '".." in path - step back',
            'Commands:',
            ]
            # Отбрасываем в выводе системные команды
            cmd_instances = list(COMMANDS.values())[:-1]
            for command in cmd_instances:
                output.append(command.help())

            emit('cmd_output', {'text': output})

    def name(self):
        return 'help'
    
    def help(self):
        name = self.name()
        return f'/{name} [command]: Displays a command info / list of available commands'


COMMANDS = {
    'default': ClearOutputCommand(tools),
    'clear': ClearAllCommand(tools),
    'help': HelpCommand(tools),
    'ls': ListCommand(tools),
    'cd': ChangeDirectoryCommand(tools),
    'mkdir': MakeDirectoryCommand(tools),
    'rmdir': RemoveDirectoryCommand(tools),
    'get': GetCommand(tools),
}

COMMANDS['not_found'] = NotFoundCommand(tools)
