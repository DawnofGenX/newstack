{{ title }}
================================================================================

{{ description }}

This site is built by Sphinx with autodoc, so the API section below is generated from
the docstrings in `src/{{ package_name }}/`, and every code block marked as a doctest is
executed during the build.

.. toctree::
   :maxdepth: 2
   :caption: Guides

   guides/counting

.. toctree::
   :maxdepth: 2
   :caption: Reference

   api

Indices
=======

* :ref:`genindex`
* :ref:`modindex`
