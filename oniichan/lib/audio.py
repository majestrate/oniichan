from subprocess import Popen, PIPE, TimeoutExpired


def convert_to_ogg(fin, fout):
    """
    convert uploaded data from file descriptor fin to vorbis file open at fout
    """
    p = Popen(['ffmpeg', '-i', fin, '-acodec', 'libvorbis', fout],
              stdout=PIPE)
    try:
        retcode = p.wait(timeout=30)
    except TimeoutExpired:
        return -1
    return retcode == 0
