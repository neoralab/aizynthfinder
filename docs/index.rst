aizynthfinder documentation
===========================

aizynthfinder is a toolkit for retrosynthetic planning. The default algorithm uses Monte Carlo tree search to recursively decompose a molecule into purchasable precursors, guided by a policy model trained on known reaction templates.

Getting started
---------------

To run retrosynthesis experiments you need both:

- a trained model or policy bundle, and
- a stock collection of purchasable precursors.

You can download the public starter assets and a matching ``config.yml`` with:

.. code-block:: bash

    download_public_data .

This command downloads the public data into the current directory and writes a ``config.yml`` file that can be used directly with the Python API and the service-layer API.

Supported interfaces
--------------------

The package is documented around two primary integration surfaces:

* the Python API for direct control of ``AiZynthFinder``
* the service-layer API for validated tool integration and structured payloads

The Python API is useful when you want fine-grained control over policy selection, search execution, scoring, and route extraction.

.. code-block:: python

    from aizynthfinder.aizynthfinder import AiZynthFinder

    finder = AiZynthFinder(configfile="config.yml")
    finder.target_smiles = "COc1cccc(OC(=O)/C=C/c2cc(OC)c(OC)c(OC)c2)c1"
    finder.prepare_tree()
    finder.tree_search()
    finder.build_routes()

    print(finder.extract_statistics())

The service layer is useful for external tools and agents that need a validated request/response contract.

.. code-block:: python

    from aizynthfinder.schemas import PlanningRequest
    from aizynthfinder.services import plan_reaction_routes

    result = plan_reaction_routes(
        PlanningRequest(
            smiles="COc1cccc(OC(=O)/C=C/c2cc(OC)c(OC)c(OC)c2)c1",
            config_file="config.yml",
            show_progress=False,
        )
    )

    print(result.model_dump_json(indent=2))

Documentation guide
-------------------

Use the sections below based on the task you are working on:

* ``python_interface`` for programming examples and API usage
* ``configuration`` for configuration files and runtime options
* ``stocks`` for stock sources and inventory setup
* ``scoring`` for route evaluation and ranking
* ``howto`` for common workflows
* ``sequences`` and ``relationships`` for route analysis outputs

.. toctree::
    :hidden:

    python_interface
    configuration
    stocks
    scoring
    howto
    sequences
    relationships
