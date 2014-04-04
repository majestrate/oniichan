from jinja2 import Environment, FileSystemLoader
from oniichan import config
import markdown
import html

_env = Environment(loader=FileSystemLoader(config.template_paths),extensions=['jinja2.ext.autoescape'])


def get(name):
    return _env.get_template(name)


def render_post(post):
    text = markdown.markdown(post.text, output_format='html5', safe_mode='escape')
    return get('board_post.html').render(post = post, text = text)
    

def generate_thread(board, posts, header, fd):
    """
    generate a thread for a board given posts
    write to file descriptor
    """
    op = posts[0]
    replies = posts[1:] if len(posts) > 1 else []
    title = op.subject or '/%s/ - %s ' % (board.name, board.long_name)
    template = get('thread.html')
    data = template.render(
        header = header,
        board = board,
        title = title,
        op = op,
        replies = replies,
        reply = str(op.post_id))
    fd.write(data)

def generate_board_page(board, threads, page_no, header, fd):
    """
    generate a board page for a board given threads and a page number
    write to file descriptor
    """
    title = '/' + board.name + '/ - ' + board.long_name
    template = get('board.html')
    data = template.render(
        header = header,
        board = board, 
        threads = threads, 
        title = title, 
        reply = '0')
    fd.write(data)

def generate_front_page(latest_posts, fd):
    """
    generate the front page with the latest posts
    write to file descriptor
    """
    #TODO: implement


    

