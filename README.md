oniichan
========

minimalist imageboard/mediaboard software 

requires: 

* python 3.4

* ffmpeg

* pip

to activate the app server in debug mode:

----

    sudo apt-get install ffmpeg

    ./activate.sh

    pip3 install -r requirements.txt

    python3 debug.py


to deploy the site with nginx and gunicorn:

----

    # all this as root

    # create oniichan system user
    adduser --system --disabled-login --home /var/www/oniichan oniichan

    # copy repo root to /var/www
    cp -rf /path/to/this/repo /var/www/

    # change owner of /var/www/oniichan to the oniichan user
    chown -R oniichan:oniichan /var/www/oniichan

    # set permissions on directories
    chmod 755 /var/www/oniichan
    chmod 700 /var/www/oniichan/prod

    # set up oniichan production virtual environment as oniichan user
    su -u oniichan -c /var/www/oniichan/prod.sh

    # copy nginx configs
    cp /var/www/oniichan/configs/nginx/oniichan /etc/nginx/sites-available/
    ln -s /etc/nginx/sites-available/oniichan /etc/nginx/sites-enabled/oniichan

    # get supervisor, this will keep the app server alive
    apt-get install supervisor

    # copy supervisor configs
    cp /var/www/oniichan/configs/supervisor/oniichan.conf /etc/supervisor/conf.d/

    # reload supervisor
    supervisorctl reread
    supervisorctl update

    # start gunicorn with oniichan via supervisor
    supervisorctl start oniichan
