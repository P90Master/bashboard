from flask import render_template
from flask_socketio import send, join_room
from werkzeug.routing import BaseConverter

from bashboard import app, db, sio
from bashboard.models import Message
from bashboard.commands import COMMANDS
from bashboard.utils import PathThreadTools


class PathConverter(BaseConverter):
    regex = r'(?:\w+\-?)*'

    def to_python(self, value):
        path_list = [x for x in value.split('-')]
        if path_list[-1]:
            return path_list

        return path_list[:-1]

    def to_url(self, value):
        if value:
            head = value[0]
            tail = value[-1]
        else:
            head = None
            tail = None
        
        if not head:
            value = value[1:]
        
        if not tail:
            value = value[:-1]
        
        return '-'.join(x for x in value)


app.url_map.converters['url_path'] = PathConverter

command_not_found = COMMANDS.get('not_found')
command_defautl = COMMANDS.get('default')
tools = PathThreadTools()


@app.route(
    '/<url_path:path>',
    methods=['GET',]
)
def index(path):
    thread = tools.thread_finder(path)
    user_location = '/'.join(path)
    if user_location:
        user_location += '/'

    messages = thread.messages[-100:]

    return render_template(
        'chat.html',
        messages=messages,
        user_location=user_location,
    )


@sio.on('join_thread')
def join_thread(data):
    path_str = data.get('path')[1:]
    path = [x for x in path_str.split('-')]
    thread = tools.thread_finder(path)

    join_room(str(thread.id))


def validate(message):
    if message and (not isinstance(message, str) or message.strip()):
        return True

    return False


@sio.on('message')
def message_handler(data):
    text = data['text']
    if not validate(text):
        return

    path_str = data['path'][1:]

    path = [x for x in path_str.split('-')]
    if not path[-1]:
        # Отбрасываем "-" в конце ссылки
        path.pop()

    thread = tools.thread_finder(path)

    if text[0] == '/':
        return command_handler(path, thread, text)

    new_msg = Message(text=text, thread_id=thread.id)
    db.session.add(new_msg)
    db.session.commit()

    send({'id': new_msg.id, 'text': text}, to=str(thread.id))


def command_handler(path, thread, command):
    # Отбрасываем "/" в начале
    # Реверсируем для взятия блоков команды через .pop()
    command_blocks = command[1:].split()[::-1]
    if not command_blocks:
        return command_defautl.execute(path=path)
    
    command_name = command_blocks.pop()
    command_instance = COMMANDS.get(command_name, command_not_found)

    return command_instance.execute(
        command_blocks=command_blocks,
        path=path,
        thread=thread,
    )
