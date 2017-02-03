.. pyxona documentation master file, created by
   sphinx-quickstart on Fri Feb  3 09:52:17 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pyxona's documentation!
==================================

Pyxona has no documentation yet.

.. doctest::
  
    >>> import pyxona
    >>> import os
    >>> import numpy as np
    >>> current_dir = os.path.dirname(".")
    >>> test_data_dir = os.path.join(current_dir, "..", "pyxona", "tests", "test_data")
    >>> axona_file_path = os.path.join(current_dir, "..", "pyxona", "tests", "axona_raw_data/DVH_2013103103.set")
    >>> def _check_array_equal(a, b):
    ...     if a.dtype == "<U1" and b.dtype == "<U1":
    ...         return (a == b).all()
    ...     else:
    ...         return ((a == b) | (np.isnan(a) & np.isnan(b))).all()
    >>> axona_file = pyxona.File(axona_file_path)    
    >>> for i, cut in enumerate(axona_file.cuts):
    ...     indices = np.load(os.path.join(test_data_dir, "cut_indices"+str(i)+".npy"))
    ...     assert _check_array_equal(indices, cut.indices)

References
----------

* :ref:`genindex`
* :ref:`search`
