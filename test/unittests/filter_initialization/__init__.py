"""Headless invariant tests for filter construction via the unified factory.

PR 0 establishes :func:`model.filters.factory.construct_filter_instance` as the single entry
point for building filters. The invariant this test package guards is: for every
:class:`model.filter.FilterTypeEnumeration` value, the factory returns either a usable filter
instance or ``None`` (for virtual-filter type codes that are deliberately not implemented
yet). Later migration PRs grow this package to assert that the returned filter's
``in_data_types`` / ``out_data_types`` are non-empty for the migrated types, which is the
regression that catches "half-initialised filter" bugs when the editor view was never opened.

The tests run headlessly: no editor view is instantiated. A ``QApplication`` is required
only because importing :mod:`model` triggers Qt-dependent transitive imports; it is spun up
once per module via :mod:`_qapp_setup` and reused across tests.

One module per filter-category test class so each file stays navigable — the previous
monolithic ``test_filter_initialization.py`` had grown past 2 700 lines.
"""
