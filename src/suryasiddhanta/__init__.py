"""
suryasiddhanta
==============
A complete Python library implementing all 14 chapters of the Surya Siddhanta,
the ancient Indian astronomical system (c. 400-600 CE).

This library faithfully implements the algorithms from the Surya Siddhanta
as translated by Ebenezer Burgess (1860), organized chapter-wise for
clarity and scholarly reference.

Nothing is re-exported at the top level: import a chapter module, or a
planet module from ``suryasiddhanta.planets``.

Quick Start:
    >>> from suryasiddhanta.ch02_true_places import compute
    >>> print(compute("Jupiter", 628, 1, 1))
    >>> from suryasiddhanta.planets import jupiter
    >>> print(jupiter.compute(628, 1, 1))

References:
    - Burgess, E. (1860). Translation of the Surya Siddhanta.
      Journal of the American Oriental Society, Vol. 6.
    - Plofker, K. (2009). Mathematics in India. Princeton UP.

Version: 2.0.0
License: MIT
"""

__version__ = "2.0.0"
__author__ = "Ashutosh Nigam"
__license__ = "MIT"
