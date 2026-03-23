Python and service APIs
=======================

AiZynthFinder supports two documented integration paths:

* the Python API for direct control over search setup and execution, and
* the service-layer API for validated inputs and structured outputs when integrating with tools or agents.

Python API
----------

Use ``AiZynthFinder`` directly when you want to control stock selection, policy selection, route scoring, and downstream analysis step by step.

.. code-block:: python

    from aizynthfinder.aizynthfinder import AiZynthFinder

    finder = AiZynthFinder(configfile="config.yml")

    finder.stock.select("zinc")
    finder.expansion_policy.select("uspto")
    finder.filter_policy.select("uspto")

    finder.target_smiles = "Cc1cccc(c1N(CC(=O)Nc2ccc(cc2)c3ncon3)C(=O)C4CCS(=O)(=O)CC4)C"
    finder.prepare_tree()
    finder.tree_search(show_progress=False)
    finder.build_routes()

    stats = finder.extract_statistics()
    routes = finder.routes.dict_with_extra(include_scores=True)

``zinc`` and ``uspto`` are configuration keys from ``config.yml``. The filter policy is optional.

The ``build_routes`` method must be called before route inspection and most downstream analysis.

Service-layer API
-----------------

Use the planning service layer when another program needs a single validated request object and a structured response payload.

.. code-block:: python

    from aizynthfinder.schemas import PlanningRequest
    from aizynthfinder.services import plan_reaction_routes

    result = plan_reaction_routes(
        PlanningRequest(
            smiles="Cc1cccc(c1N(CC(=O)Nc2ccc(cc2)c3ncon3)C(=O)C4CCS(=O)(=O)CC4)C",
            config_file="config.yml",
            show_progress=False,
        )
    )

    print(result.solved)
    print(result.statistics)
    print(result.stock_info)
    print(result.routes)

This service API wraps the synchronous planning workflow and returns a validated ``PlanningResult`` payload that is convenient for tool integration.

Further reading
---------------

The docstrings of modules, classes, and methods can be consulted :doc:`here <aizynthfinder>`.

You can also inspect them interactively:

.. code-block:: python

    from aizynthfinder.chem import Molecule
    help(Molecule)
    help(Molecule.fingerprint)

If you are interested in the relationships between classes, see :doc:`relationships`. For more detail on the main algorithmic flows, see :doc:`sequences`.
