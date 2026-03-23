import pytest

from aizynthfinder.chem import SmilesBasedRetroReaction, TreeMolecule
from aizynthfinder.context.policy import (
    ExpansionStrategy,
    MultiExpansionStrategy,
    TemplateBasedExpansionStrategy,
)
from aizynthfinder.utils.exceptions import PolicyException


class _StaticExpansionStrategy(ExpansionStrategy):
    def __init__(self, key, config, reaction_smiles_priors):
        super().__init__(key, config)
        self._reaction_smiles_priors = reaction_smiles_priors

    def get_actions(self, molecules, cache_molecules=None):
        mol = molecules[0]
        actions = []
        priors = []
        for index, (reactants, prior) in enumerate(self._reaction_smiles_priors):
            actions.append(
                SmilesBasedRetroReaction(
                    mol,
                    reactants_str=reactants,
                    metadata={"policy_name": self.key, "rank": index},
                )
            )
            priors.append(prior)
        return actions, priors


def test_multi_expansion_strategy_incorrect_keys(
    default_config, setup_template_expansion_policy
):
    expansion_policy = default_config.expansion_policy
    strategy1, _ = setup_template_expansion_policy("policy1")
    expansion_policy.load(strategy1)

    with pytest.raises(ValueError, match="expansion strategy keys must exist"):
        multi_expansion_strategy = MultiExpansionStrategy(
            "multi_expansion_strategy",
            default_config,
            expansion_strategies=["policy1", "policy2"],
        )
        mols = [TreeMolecule(smiles="CCO", parent=None)]
        multi_expansion_strategy.get_actions(mols)


def test_multi_expansion_strategy(default_config, setup_template_expansion_policy):
    expansion_policy = default_config.expansion_policy
    strategy1, _ = setup_template_expansion_policy("policy1")
    expansion_policy.load(strategy1)
    strategy2, _ = setup_template_expansion_policy("policy2")
    expansion_policy.load(strategy2)
    strategy3, _ = setup_template_expansion_policy("policy3")
    expansion_policy.load(strategy3)

    multi_expansion_strategy = MultiExpansionStrategy(
        "multi_expansion_strategy",
        default_config,
        expansion_strategies=["policy1", "policy2"],
    )
    multi_expansion_strategy.additive_expansion = True

    mols = [TreeMolecule(smiles="CCO", parent=None)]
    _, priors = multi_expansion_strategy.get_actions(mols)

    assert priors == [0.7, 0.2, 0.7, 0.2]


def test_multi_expansion_strategy_wo_additive_expansion(
    default_config, setup_template_expansion_policy
):
    expansion_policy = default_config.expansion_policy
    strategy1, _ = setup_template_expansion_policy("policy1")
    expansion_policy.load(strategy1)
    strategy2, _ = setup_template_expansion_policy("policy2")
    expansion_policy.load(strategy2)

    multi_expansion_strategy = MultiExpansionStrategy(
        "multi_expansion_strategy",
        default_config,
        expansion_strategies=["policy1", "policy2"],
    )

    mols = [TreeMolecule(smiles="CCO", parent=None)]
    _, priors = multi_expansion_strategy.get_actions(mols)

    assert priors == [0.7, 0.2]


def test_multi_expansion_strategy_non_additive_uses_weighted_first_policy(
    default_config, setup_template_expansion_policy
):
    expansion_policy = default_config.expansion_policy
    strategy1, _ = setup_template_expansion_policy("policy1")
    expansion_policy.load(strategy1)
    strategy2, _ = setup_template_expansion_policy("policy2")
    expansion_policy.load(strategy2)

    multi_expansion_strategy = MultiExpansionStrategy(
        "multi_expansion_strategy",
        default_config,
        expansion_strategies=["policy1", "policy2"],
        expansion_strategy_weights=[0.25, 0.75],
    )

    mols = [TreeMolecule(smiles="CCO", parent=None)]
    _, priors = multi_expansion_strategy.get_actions(mols)

    priors = [round(p, 4) for p in priors]
    assert priors == [0.1944, 0.0556]


def test_weighted_multi_expansion_strategy(
    default_config, setup_template_expansion_policy
):
    expansion_policy = default_config.expansion_policy
    strategy1, _ = setup_template_expansion_policy("policy1")
    expansion_policy.load(strategy1)
    strategy2, _ = setup_template_expansion_policy("policy2")
    expansion_policy.load(strategy2)

    multi_expansion_strategy = MultiExpansionStrategy(
        "multi_expansion_strategy",
        default_config,
        expansion_strategies=["policy1", "policy2"],
        expansion_strategy_weights=[0.25, 0.75],
    )
    multi_expansion_strategy.additive_expansion = True

    mols = [TreeMolecule(smiles="CCO", parent=None)]
    _, priors = multi_expansion_strategy.get_actions(mols)

    priors = [round(p, 4) for p in priors]
    assert priors == [0.1944, 0.0556, 0.5833, 0.1667]


def test_weighted_multi_expansion_strategy_wrong_weights(
    default_config, setup_template_expansion_policy
):
    expansion_policy = default_config.expansion_policy
    strategy1, _ = setup_template_expansion_policy("policy1")
    expansion_policy.load(strategy1)
    strategy2, _ = setup_template_expansion_policy("policy2")
    expansion_policy.load(strategy2)

    with pytest.raises(
        ValueError,
        match="The expansion strategy weights in MultiExpansion should sum to one. ",
    ):
        multi_expansion_strategy = MultiExpansionStrategy(
            "multi_expansion_strategy",
            default_config,
            expansion_strategies=["policy1", "policy2"],
            expansion_strategy_weights=[0.2, 0.7],
        )


def test_weighted_multi_expansion_strategy_accepts_float_rounding(
    default_config, setup_template_expansion_policy
):
    expansion_policy = default_config.expansion_policy
    strategy1, _ = setup_template_expansion_policy("policy1")
    expansion_policy.load(strategy1)
    strategy2, _ = setup_template_expansion_policy("policy2")
    expansion_policy.load(strategy2)

    multi_expansion_strategy = MultiExpansionStrategy(
        "multi_expansion_strategy",
        default_config,
        expansion_strategies=["policy1", "policy2"],
        expansion_strategy_weights=[0.1 + 0.2, 0.7],
    )

    assert multi_expansion_strategy.expansion_strategy_weights == [0.30000000000000004, 0.7]


def test_weighted_multi_expansion_strategy_requires_matching_lengths(
    default_config, setup_template_expansion_policy
):
    expansion_policy = default_config.expansion_policy
    strategy1, _ = setup_template_expansion_policy("policy1")
    expansion_policy.load(strategy1)
    strategy2, _ = setup_template_expansion_policy("policy2")
    expansion_policy.load(strategy2)

    with pytest.raises(
        ValueError,
        match="number of expansion strategy weights in MultiExpansion must match",
    ):
        MultiExpansionStrategy(
            "multi_expansion_strategy",
            default_config,
            expansion_strategies=["policy1", "policy2"],
            expansion_strategy_weights=[1.0],
        )


def test_multi_expansion_strategy_cutoff(
    default_config, setup_template_expansion_policy
):
    expansion_policy = default_config.expansion_policy
    strategy1, _ = setup_template_expansion_policy("policy1")
    expansion_policy.load(strategy1)
    strategy2, _ = setup_template_expansion_policy("policy2")
    expansion_policy.load(strategy2)

    multi_expansion_strategy = MultiExpansionStrategy(
        "multi_expansion_strategy",
        default_config,
        expansion_strategies=["policy1", "policy2"],
        additive_expansion=True,
        cutoff_number=4,
    )

    mols = [TreeMolecule(smiles="CCO", parent=None)]
    actions, priors = multi_expansion_strategy.get_actions(mols)

    assert len(actions) == 4
    assert len(priors) == 4

    multi_expansion_strategy = MultiExpansionStrategy(
        "multi_expansion_strategy",
        default_config,
        expansion_strategies=["policy1", "policy2"],
        additive_expansion=True,
        cutoff_number=2,
    )
    actions, priors = multi_expansion_strategy.get_actions(mols)
    assert len(actions) == 2
    assert len(priors) == 2


def test_multi_expansion_strategy_deduplicates_actions_before_pruning(default_config):
    mol = TreeMolecule(smiles="CCO", parent=None)
    policy1 = _StaticExpansionStrategy(
        "policy1",
        default_config,
        [("CC.C", 0.9), ("CO.C", 0.4)],
    )
    policy2 = _StaticExpansionStrategy(
        "policy2",
        default_config,
        [("CC.C", 0.6), ("CN.O", 0.5)],
    )
    default_config.expansion_policy.load(policy1)
    default_config.expansion_policy.load(policy2)

    multi_expansion_strategy = MultiExpansionStrategy(
        "multi_expansion_strategy",
        default_config,
        expansion_strategies=["policy1", "policy2"],
        expansion_strategy_weights=[0.4, 0.6],
        additive_expansion=True,
        cutoff_number=2,
    )

    actions, priors = multi_expansion_strategy.get_actions([mol])

    assert len(actions) == 2
    assert [round(prior, 4) for prior in priors] == [0.36, 0.3]
    assert actions[0].metadata["policy_names"] == ["policy1", "policy2"]
    assert actions[0].metadata["prior_merged_from"] == [0.36, 0.18]


def test_create_templated_expansion_strategy_wo_kwargs():
    with pytest.raises(
        PolicyException, match=" class needs to be initiated with keyword arguments"
    ):
        _ = TemplateBasedExpansionStrategy("dummy", None)


def test_load_templated_expansion_strategy(
    default_config, setup_template_expansion_policy
):
    strategy, mocked_onnx_model = setup_template_expansion_policy()
    mocked_onnx_model.assert_called_once()
    assert len(strategy.templates) == 3


def test_load_invalid_templated_expansion_strategy(
    default_config, create_dummy_templates, mock_onnx_model
):
    templates_filename = create_dummy_templates(4)
    with pytest.raises(PolicyException):
        TemplateBasedExpansionStrategy(
            "policy1",
            default_config,
            model="dummy.onnx",
            template=templates_filename,
        )


def test_load_templated_expansion_strategy_from_csv(
    default_config, mock_onnx_model, tmpdir
):
    templates_filename = str(tmpdir / "temp.csv")

    with open(templates_filename, "w") as fileobj:
        fileobj.write("template_index\ttemplate\tmetadata\n")
        fileobj.write("0\tAAA\tmetadata1\n")
        fileobj.write("1\tBBB\tmetadata2\n")
        fileobj.write("2\tCCC\tmetadata3\n")

    strategy = TemplateBasedExpansionStrategy(
        "default", default_config, model="dummy.onnx", template=templates_filename
    )

    assert len(strategy.templates) == 3
    assert list(strategy.templates.columns) == ["template", "metadata"]
