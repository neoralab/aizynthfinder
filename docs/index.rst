aizynthfinder documentation
===========================

aizynthfinder is a tool for retrosynthetic planning. The default algorithm is based on a Monte Carlo tree search that recursively breaks down a molecule to purchasable precursors. The tree search is guided by a policy that suggests possible precursors by utilizing a neural network trained on a library of known reaction templates.

Introduction
------------

To run retrosynthesis experiments you need a trained model and a stock collection. You can download a publicly available model based on USPTO and a stock collection from the ZINC database.

.. code-block::

    download_public_data .

This downloads the data to your current directory. The resulting ``config.yml`` file can be used directly with the Python and service-layer APIs.

The package is documented around two supported integration surfaces:

* the Python API for direct control of ``AiZynthFinder``, and
* the service-layer API for validated tool integration and structured payloads.

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


.. toctree::
    :hidden:
    
    python_interface
    configuration
    stocks
    scoring
    howto
    aizynthfinder
    sequences
    relationships
