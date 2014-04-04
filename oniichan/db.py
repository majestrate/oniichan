from oniichan import templates
from oniichan import util
from oniichan import config
from sqlalchemy import create_engine, asc, desc
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text
from sqlalchemy.schema import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import operator
import os

_engine = create_engine('sqlite:////var/lib/oniichan/oniichan.db3')

make_session = sessionmaker(bind=_engine)

_Base = declarative_base()

@contextmanager
def open():
    sess = make_session()
    yield session(sess)
    sess.close()

class session:

    def __init__(self, sess):
        self.sess = sess
        self.query = sess.query
        self.execute = sess.execute
        self.add = sess.add
        
    def commit(self):
        self.sess.commit()

    def get_spam_strings(self):
        #TODO: implement
        return []

    def get_all_board_names(self):
        """
        return a list of all boards with their short names
        """
        for board in self.sess.query(Board).all():
            yield board.name

    def get_board_by_id(self, board_id):
        """
        get a board object by thier id
        """
        return self.sess.query
            
    def get_board_by_name(self, name):
        """
        get a board object by their short name
        """
        return self.sess.query(Board).filter(Board.name == name).first()

    def check_mod_login(self, username, password):
        """
        verify a mod login
        """
        user = self.sess.query(ModUser).filter(ModUser.username == username).first()
        return user is not None and user.password == util.hash_func(password, user.salt)
        
        
    def new_mod(self, username, password):
        """
        create new mod with credentials
        return None if already exists
        """
        if self.sess.query(ModUser).filter(ModUser.username == username).count() > 0:
            return
        user = ModUser()
        user.username = username
        user.salt = util.new_salt()
        user.password = util.hash_func(password, user.salt)
        self.sess.add(user)
        return user

    def new_board(self, name):
        if self.sess.query(Board).filter(Board.name == name).count() > 0:
            return
        board = Board()
        board.name = name
        board.post_no = 0
        self.sess.add(board)
        self.sess.commit()
        return board


    def delete_board(self, board):
        if isinstance(board,str):
            board = self.get_board_by_name(board)
        if board is not None:
            self.sess.execute("DELETE FROM posts WHERE board_id=:id",{'id':board.id})
            #sess.execute("DELETE FROM boards WHERE id=:id",{'id':board.id})
            self.sess.delete(board)

    def delete_post(self, post):
        if post.reply_id == 0:
            sess.execute('DELETE FROM posts WHERE reply_id=:post_id',{'post_id':post.post_id})
        #sess.execute('DELETE FROM posts WHERE post_id=:post_id',{'post_id':post.post_id})
        self.sess.delete(post)
            

class ModUser(_Base):
    __tablename__ = 'modusers'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)
    salt = Column(String)
    

class Board(_Base):
    __tablename__ = 'boards'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    long_name = Column(String)
    description = Column(String)
    post_no = Column(Integer)

    def get_dir(self):
        return os.path.join(config.board_base_dir,self.name)

    def get_threads_per_page(self):
        return 5

    def get_fname_for_page(self, page_no):
        return os.path.join(self.get_dir(),'%s.html' % page_no)

    def get_post(self, sess, post_id):
        return sess.query(Post).filter(Post.board_id == self.id, Post.post_id == post_id).first()
    
    def new_post(self,sess, reply=None):
        self.post_no += 1
        sess.commit()
        post = Post()
        post.reply_id = 0 if reply is None else int(reply)
        post.board_id = self.id
        post.post_id = self.post_no
        post.date = util.datetime_now()
        sess.add(post)
        return post

    def get_threads(self, sess):
        threads = []
        for op in sess.query(Post).filter(Post.board_id == self.id, Post.reply_id == 0).all():
            thread = [op]
            for reply in sess.query(Post).filter(Post.board_id == self.id, Post.reply_id == op.post_id).order_by(asc(Post.date)).all():
                thread.append(reply)
            threads.append(thread)
        
        return list(sorted(threads, key=operator.itemgetter(-1), reverse = True))

    def _get_all_post_ids(self, sess):
        yield from sess.query(Thread).from_statement(
            "SELECT id FROM posts WHERE board_id=:id").params(id=self.id).all()

class Post(_Base):
    __tablename__ = 'posts'
    internal_id = Column(Integer, primary_key=True)
    post_id = Column(Integer)
    board_id = Column(Integer, ForeignKey('boards.id'))
    reply_id = Column(Integer)
    date = Column(DateTime)
    text = Column(Text)
    subject = Column(String)
    name = Column(String)
    email = Column(String)
    fname = Column(String)
    fpath = Column(String)
    desthash = Column(String)

    def __lt__(self, post):
        return self.date < post.date

    def __gt__(self, post):
        return self.date > post.date
        
    def __le__(self, post):
        return self.date <= post.date
        
    def __ge__(self, post):
        return self.date >= post.date

    def has_file(self):
        return self.fname is not None and self.fpath is not None

    def is_i2p(self):
        return self.desthash is not None

    def render(self):
        return templates.render_post(self)
    
    def get_file_url(self):
        if self.fpath is None:
            return ''
        else:
            return '/media/%s' % self.fpath.split('/')[-1]

    def getDate(self):
        return str(self.date).split('.')[0]

    def get_thread_path(self, sess):
        board = sess.query(Board).filter(Board.id == self.board_id).first()
        id = self.post_id if self.reply_id == 0 else self.reply_id
        return os.path.join(board.get_dir(),'thread-%s.html' % id)

    def get_url(self, sess):
        board = sess.query(Board).filter(Board.id == self.board_id).first()
        id = self.post_id if self.reply_id == 0 else self.reply_id
        return '/%s/thread-%s.html' % ( board.name, id)



_Base.metadata.create_all(_engine)
