Architecture
============

.. toctree::
   :maxdepth: 2


Database
--------

Updates and Changes
~~~~~~~~~~~~~~~~~~~

0.3 Updates
^^^^^^^^^^^

- **Address** has been renamed to **Location**, and changed to allow **Person**
  and **Account** to have one or more **Address**, which is a Location
  with optional start/end dates.
- **Subscribe** event has been renamed to **Subscription**; subscription type
  field has been converted from a Django choice field to the
  editable **SubscriptionType**.
- Subscription **duration** has been converted from months and fraction of months
  to the actual days between start and end dates.


0.2 Updates
^^^^^^^^^^^

The overall architectures of the schema remains the same, but several fields were
made less restrictive to accommodate variation in the Logbook data. These include:

- Reimbursement price (now optional)
- Subscribe duration
- Options were provided for Subscribe sub_type fields, as well as for modification.


Database Diagrams
~~~~~~~~~~~~~~~~~

.. NOTE::
    Detail charts are generated with `DAVILA <https://github.com/jabauer/DAVILA>`_.
    The ``sphinx-docs`` directory includes a ``customize.csv`` and MySQL dump
    that was used to generate the following schema diagrams.

Initial Schema Design (Version 004)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. image:: _static/mep-schema-004.png
    :target: _static/mep-schema-004.png
    :alt: MEP Schema Design 004

.. NOTE::
    This does not include additional complexity of URLs for people records
    per 19 June 2017 project meeting.


Database Overview (v0.3)
^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: _static/db-overview-v03.png
    :target: _static/db-overview-v03.png
    :alt: MEP Schema Overview v0.3


Person detail (v0.3)
^^^^^^^^^^^^^^^^^^^^

.. image:: _static/db-people-v03.png
    :target: _static/db-people-v03.png
    :alt: MEP Schema - Person detail v0.3

Account detail (v0.3)
^^^^^^^^^^^^^^^^^^^^^

.. image:: _static/db-accounts-v03.png
    :target: _static/db-accounts-v03.png
    :alt: MEP Schema - Account detail v0.3

Book detail (v0.3)
^^^^^^^^^^^^^^^^^^^^^

.. image:: _static/db-books-v03.png
    :target: _static/db-books-v03.png
    :alt: MEP Schema - Book detail v0.3


Previous versions
~~~~~~~~~~~~~~~~~

People Detail (0004)
^^^^^^^^^^^^^^^^^^^^
.. image:: _static/people-module-004.png
    :target: _static/people-module-004.png
    :alt: People Module Detail

.. NOTE::
    :class:`~mep.people.models.InfoURL` now includes a required ``name`` field


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
