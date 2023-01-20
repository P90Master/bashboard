from bashboard import app, db
from bashboard.models import Message, Thread


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'Message': Message,
        'Thread': Thread,
    }
