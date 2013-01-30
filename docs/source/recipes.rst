provy Recipes
=============

Django + Nginx same server
--------------------------

.. image:: images/django-nginx-recipe.png

This recipe features a django website with 4 processes and 2 threads per process.

Nginx serves the requests via reverse proxy, while load balancing the 4 processes.

Each django process is a gunicorn process bound to a port ranging from 8000-8003.

Django's static files are served using nginx.

To read more about this recipe, :doc:`click here </recipes/django-1-server>`.