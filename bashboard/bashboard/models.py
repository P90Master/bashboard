from bashboard import db
from sqlalchemy_utils import LtreeType
from sqlalchemy_utils import Ltree


id_seq = db.Sequence('thread_id_seq')


class Thread(db.Model):
    __tablename__ = 'thread'
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(LtreeType, nullable=False, unique=True)
    name = db.Column(db.String(32), nullable=False, index=True)
    parent = db.relationship(
        'Thread',
        primaryjoin = db.remote(path) == db.foreign(db.func.subpath(path, 0, -1)),
        backref=db.backref('subthreads', cascade='all, delete-orphan'),
    )

    def __init__(self, name, parent=None):
        _id = db.session.execute(id_seq)
        self.id = _id
        self.name = name
        ltree_id = Ltree(str(name))
        self.path = ltree_id if parent is None else parent.path + ltree_id

    def __repr__(self):
        return '<id {}, thread "{}", Path "{}">'.format(self.id, self.name, self.path)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.String(1024), nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'))

    thread = db.relationship(
        'Thread',
        primaryjoin = Thread.id == thread_id,
        backref=db.backref('messages', cascade='all, delete-orphan')
    )

    def __repr__(self):
        return '<id {}, Message "{}">'.format(self.id, self.text)
