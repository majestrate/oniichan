from oniichan import app
from oniichan import db
from oniichan import templates
from oniichan import config
from oniichan import spam
from oniichan import util
from oniichan.lib import audio
import flask
from werkzeug.utils import secure_filename
from functools import wraps
import io
import os
import string

MOD_KEY = 'mod_username'
RATELIMIT_KEY = 'ratelimit'
I2P_HEADER = 'X-I2P-DestHash'

@app.route('/ib/')
def oniichan_kitteh_face():
    return ':3'

@app.route('/ib/mod', methods=['GET','POST'])
def oniichan_mod_panel():
    if flask.request.method == 'POST':
        form = flask.request.form
        if 'username' in form and 'password' in form:
            username = form['username']
            password = form['password']

            with db.open() as session:
                if session.check_mod_login(username, password):
                    flask.session[MOD_KEY] = username
                else:
                    flask.flash('incorrect login')
        return flask.redirect('/ib/mod')
    elif MOD_KEY in flask.session:
        return flask.render_template('mod_panel.html')
    else:
        return flask.render_template('mod_login.html')

@app.route('/ib/mod/toggle_tor')
def oniichan_toggle_tor():
    if MOD_KEY in flask.session:
        config.enable_tor = not config.enable_tor
        flask.flash('tor posting = %s' % config.enable_tor)
    return flask.redirect('/ib/mod')

@app.route('/ib/mod/regen')
def oniichan_mod_regen_boards():
    if MOD_KEY in flask.session:
        regen_boards()
        flask.flash('regenerated boards')
    return flask.redirect('/ib/mod')

@app.route('/ib/mod/logout')
def oniichan_mod_logout():
    if MOD_KEY in flask.session:
        del flask.session[MOD_KEY]
        flask.flash('logged out')
    return flask.redirect('/ib/mod')

@app.route('/ib/mod/create_mod', methods=['POST'])
def oniichan_mod_create():
    if MOD_KEY in flask.session:
        form = flask.request.form
        if 'username' in form and 'password' in form:
            username = form['username']
            password = form['password']
            err = False
            if len(username) == 0:
                err = True
                flask.flash('username is blank')
            if len(password) < 6:
                err = True
                flask.flash('password too short')
            if not err:
                app.logger.info('new mod {}'.format(username))
                with db.open() as session:
                    session.new_mod(username, password)
                    session.commit()
                    flask.flash('made mod')
                    
        else:
            flask.flash('no username/password provided')
    return flask.redirect('/ib/mod')

@app.route('/ib/mod/new_board', methods=['POST'])
def oniichan_mod_new_board():
    if MOD_KEY in flask.session:
        form = flask.request.form
        err = False
        for attr in ['name', 'long_name', 'description']:
            if attr not in form:
                flask.flash('missing {}'.format(attr))
            elif len(form[attr]) == 0:
                flask.flash('{} is empty'.format(attr))
            else:
                val = form[attr]
                for c in val:
                    if attr == 'description' and c == ' ':
                        continue
                    if c not in string.ascii_letters:
                        flask.flash('{} contains bad character'.format(attr))
                        err = True
                        break
        if not err:
            app.logger.info('create new board {}'.format(form['name']))
            with db.open() as session:
                board = session.new_board(form['name'])
                if board is None:
                    flask.flash('board exists')
                else:
                    board.long_name = form['long_name']
                    board.description = form['description']
                    app.logger.info('making directories')
                    board_dir = board.get_dir()
                    if not os.path.exists(board_dir):
                        os.mkdir(board_dir)

                    app.logger.info('making root post')
                    post = board.new_post(session)
                    post.name = 'Admin'
                    post.text = 'New Board'
                    session.commit()

                    regen_boards([form['name']])
                    flask.flash('made board {}'.format(board.name))

    return flask.redirect('/ib/mod')

@app.route('/ib/mod/delete_board/<name>')
def oniichan_del_board(name):
    if MOD_KEY in flask.session:
        app.logger.info('%s deletes board %s' % (flask.session[MOD_KEY], name))
        with db.open() as session:
            board = session.get_board_by_name(name)
            if board is None:
                flask.flash('no such board')
            else:
                board_dir = board.get_dir()
                session.delete_board(board)
                session.commit()
                app.logger.debug('recursive delete %s' % board_dir)
                util.recursive_delete(board_dir)
                flask.flash('board deleted')
    return flask.redirect('/ib/mod')

@app.route('/ib/mod/delete_post/<board_name>/<int:post_id>')
def oniichan_mod_delete(board_name, post_id):
    if MOD_KEY in flask.session:
        with db.open() as session:
            board = session.get_board_by_name(board_name)
            if board is None:
                flask.flash('no such board')
            else:
                post = board.get_post(session, post_id)
                if post is None:
                    flask.flash('no such post')
                else:
                    session.delete_post(post)
                    session.commit()
                    app.logger.info('%s deteled %s/%s' % (flask.session[MOD_KEY], board_name, post_id))
                    regen_boards([board.name]) #TODO: cross board links?
                    flask.flash('post %s/%s deleted' % (board_name, post_id))
                    
    return flask.redirect('/ib/mod')
                

def error(msg):
    app.logger.info('error: %s' % msg)
    return flask.render_template('error.html', msg=msg, header={})



@app.route('/ib/post/<board_name>', methods=['POST'])
def oniichan_post(board_name):

    headers = flask.request.headers
    desthash = None
    if I2P_HEADER in headers and util.is_from_i2p(flask.request.remote_addr):
        desthash = headers[I2P_HEADER]
    
    if config.enable_tor is False and desthash is None:
        return error('posting from tor disabled temporarily')

    if RATELIMIT_KEY not in flask.session:
        flask.session[RATELIMIT_KEY] = util.now()
    else:
        lastpost = flask.session[RATELIMIT_KEY]
        flask.session[RATELIMIT_KEY] = util.now()
        app.logger.debug('lastpost = %d ' % lastpost)
        if util.now() - lastpost < config.post_ratelimit:
            return error('flood')


    # check for board
    with db.open() as session:
        if session.get_board_by_name(board_name) is None:
            return error('no such board')

    # validate form info
    form = flask.request.form
    try:
        if 'name' not in form:
            return error('no name?')
        name = form['name'].strip()
        spam.detect(name)
        if len(name) == 0:
            name = 'Anonymous'

        if 'subject' not in form:
            return error('no subject?')
        subject = form['subject'].strip()
        spam.detect(subject)
        if len(subject) == 0:
            subject = None

        if 'email' not in form:
            return error('no email?')
        email = form['email'].strip()
        spam.detect(email)
        if len(email) == 0:
            email = None

        if 'post' not in form:
            return error('no post?')
        post_text = form['post'].strip()
        if len(post_text) == 0:
            return error('no post text')
        spam.detect(post_text,True)

        if 'name' not in form:
            return error('no name?')
        reply_to = form['reply']

        files = flask.request.files
        
        fname = None
        fpath = None
        app.logger.debug('files=%s' % files)
        if 'audio' in files and len(files['audio'].filename) > 0:
            fin = files['audio']
            if 'image' in fin.mimetype:
                return error('only audio uploads are allowed right now')

            fname = secure_filename(fin.filename)
            fpath = os.path.join(config.media_dir, '%d.ogg' % util.now())
            temp_fname = os.path.join('/tmp',fpath.split('/')[-1])
            app.logger.debug('uploading file %s to %s' % (fname, fpath))
            fin.save(temp_fname)            
            result = audio.convert_to_ogg(temp_fname,fpath)
            os.unlink(temp_fname)
            if result:
                app.logger.info('upload success')
            else:
                return error('upload failed :<')

    except spam.DetectedSpam: # got spam?
        return error('your post looks like spam')
    else: # commit post and regen
        with db.open() as session:
            board = session.get_board_by_name(board_name)
            template_name = 'post.html'
            post = board.new_post(session)
            if post is None:
                return error('no such thread')
            else:
                post.reply_id = reply_to
                post.name = name
                post.subject = subject
                post.email = email
                post.text = post_text
                post.fpath = fpath
                post.fname = fname
                post.desthash = desthash

                session.commit()

                post_url = post.get_url(session)
                regen = [board.name]

        regen_boards(regen)
        return flask.redirect(post_url)

def regen_boards(boards=None):
    if boards is None:
        with db.open() as session:
            boards = session.get_all_board_names()
    with db.open() as session:
        
        header = {'boards' : [] }
        for board_name in session.get_all_board_names():
            header['boards'].append(session.get_board_by_name(board_name))

        for board_name in boards:
            app.logger.debug('regen board %s' % board_name)
            board = session.get_board_by_name(board_name)

            assert board is not None
            per_page = board.get_threads_per_page()
            thread_counter = 0
            page_threads = []
            pages = []
            threads = board.get_threads(session)
            app.logger.debug('got %d threads' % len(threads))
            app.logger.debug('threads=%s' % threads)

            render_threads = []
            for thread in threads:
                op = thread[0]
                t_fname = op.get_thread_path(session)
                render_threads.append((board, thread, t_fname))
                posts = {'op':op}
                replies = []
                t_len = len(thread)
                if t_len > 5:
                    for post in thread[-5:]:
                        replies.append(post)
                elif t_len > 1:
                    for post in thread[1-t_len:]:
                        replies.append(post)
                posts['replies'] = replies
                
                page_threads.append(posts)
                thread_counter += 1
                if thread_counter == per_page:
                    thread_counter = 0
                    pages.append(page_threads)
                    page_threads = []
                    
            if len(pages) == 0:
                pages = [page_threads]
            page_no = 0
            
            header['pages'] = list(range(len(pages)))

            for board, thread, t_fname in render_threads:
                with open(t_fname, 'w') as w:
                    app.logger.debug('generate thread %s with %d replies' % (t_fname, len(thread)))
                    templates.generate_thread(board, thread, header, w)

            for page in pages:
                app.logger.debug('generate page %d' % page_no)
                app.logger.debug('we have %d posts' % len(page))
                fname = board.get_fname_for_page(page_no)
                with open(fname,'w') as w:
                    app.logger.debug('write to %s' % fname)
                    templates.generate_board_page(board, page, page_no, header, w)
                    app.logger.debug('okay')
                    page_no += 1

            index_html = os.path.join(config.board_base_dir,board.name,'index.html')
            if not os.path.exists(index_html):
                os.symlink(board.get_fname_for_page(0), index_html)
