Architecture
============

.. toctree::
   :maxdepth: 2


Database
--------


Initial Schema (Version 004)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. image:: _static/mep-schema-004.png
    :target: _static/mep-schema-004.png
    :alt: MEP Schema Design 004

*NOTE: This does not include additional complexity of URLs for people records per 19 June 2017 project meeting*

Detail charts are generated in `DAVILA <https://github.com/jabauer/DAVILA>`_.
The ``sphinx-docs`` directory includes a ``customize.csv`` and MySQL dump that was used
to generate the following schemata.

People Detail (0004)
^^^^^^^^^^^^^^^^^^^^
.. image:: _static/people-module-004.png
    :target: _static/people-module-004.png
    :alt: People Module Detail

*ERRATA: :class:`~mep.people.models.InfoURL` now includes a required ``name`` field*


Books Detail (0004)
^^^^^^^^^^^^^^^^^^^^
.. image:: _static/books-module-004.png
    :target: _static/books-module-004.png
    :alt: Books Module Detail

Account Detail (0004)
^^^^^^^^^^^^^^^^^^^^^
.. image:: _static/accounts-module-004.png
    :target: _static/accounts-module-004.png
    :alt: Account Module Detail
