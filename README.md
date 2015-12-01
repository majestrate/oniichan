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

    pip install -r requirements.txt

    ./run.py


to deploy the site with nginx:

----

    cp -av /path/to/this/repo /var/www/
    cp /var/www/oniichan/configs/nginx/oniichan /etc/nginx/sites-available/
    ln -s /etc/nginx/sites-available/oniichan /etc/nginx/sites-enabled/oniichan
