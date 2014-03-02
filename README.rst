Setquery
========

Setquery is a utility library for evaluating single expressions composed of patterns and operators across sets, allowing user expressivity beyond what command-line arguments can express.

Development
-----------

To prepare an environment variable you must have nose and rednose installed::

  $ virtualenv .
  $ . bin/activate
  (setquery)$ pip install nose rednose
  (setquery)$ python setup.py -q nosetests
  .............
  -----------------------------------------------------------------
  13 tests run in 0.0 seconds (13 tests passed)
