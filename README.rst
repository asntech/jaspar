JASPAR 2018
===========

The JASPAR is a database of curated, non-redundant set of profiles, derived from published collections of experimentally defined transcription factor binding sites for eukaryotes.

This is the source code of JASPAR 2018 website developed in Python/Django. To run the website locally, you need to install Django and a list of other Python packages which are listed in the requirements.txt file.


Get the development version from `Bitbucket`
--------------------------------------------

If you have `git` and `pip` installed, use this:

.. code-block:: bash

    git clone https://bitbucket.org/CBGR/jaspar.git
    cd jaspar
    pip install -r requirements.txt
    mkdir temp
    chmod -R 755 ./temp
    python manage.py migrate
    python manage.py runserver

Then copy the following URL in your browser.

.. code-block:: bash

    http://127.0.0.1:8000/

Set the BIN_DIR in ./jaspar/jaspar/settings.py, which is the absolute path for analysis tools (stamp, pwm randomizer, matrix aligner). By default it is set to 'BASE_DIR/bin'

To deploy the app on a server with Apache and mod_wsgi please read this https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/modwsgi/​​

.. figure:: https://bytebucket.org/CBGR/jaspar/raw/1b1d9b317cd732793b434d0058cffaecd13fdd31/static/img/jaspar2018_home.png
   :width: 800px
   :align: left

