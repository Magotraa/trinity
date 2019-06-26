import pytest

from eth_utils import (
    ValidationError,
)

import ssz

from eth2._utils.hash import (
    hash_eth2,
)
from eth2._utils.merkle.common import (
    get_merkle_proof,
)
from eth2._utils.merkle.sparse import (
    calc_merkle_tree_from_leaves,
    get_merkle_root,
)

from eth2.beacon.deposit_helpers import (
    process_deposit,
    validate_deposit_proof,
)
from eth2.beacon.types.forks import Fork
from eth2.beacon.types.states import BeaconState
from eth2.beacon.types.deposits import Deposit

from eth2.beacon.tools.builder.validator import (
    create_mock_deposit_data,
)


def create_mock_deposit(config,
                        sample_beacon_state_params,
                        keymap,
                        pubkeys,
                        withdrawal_credentials,
                        validator_index):
    state = BeaconState(**sample_beacon_state_params).copy(
        slot=1,
        validators=(),
    )
    fork = Fork(
        previous_version=config.GENESIS_FORK_VERSION.to_bytes(4, 'little'),
        current_version=config.GENESIS_FORK_VERSION.to_bytes(4, 'little'),
        epoch=config.GENESIS_EPOCH,
    )
    deposit_data = create_mock_deposit_data(
        config=config,
        pubkeys=pubkeys,
        keymap=keymap,
        validator_index=validator_index,
        withdrawal_credentials=withdrawal_credentials,
        fork=fork,
    )

    item = hash_eth2(ssz.encode(deposit_data))
    test_deposit_data_leaves = (item,)
    tree = calc_merkle_tree_from_leaves(test_deposit_data_leaves)
    root = get_merkle_root(test_deposit_data_leaves)
    proof = list(get_merkle_proof(tree, item_index=validator_index))

    state = state.copy(
        eth1_data=state.eth1_data.copy(
            deposit_root=root,
        ),
    )

    deposit = Deposit(
        proof=proof,
        index=validator_index,
        deposit_data=deposit_data,
    )

    return state, deposit


@pytest.mark.parametrize(
    (
        'deposit_index',
        'success',
    ),
    [
        (0, True),
        (1, False),
    ]
)
def test_validate_deposit_proof(config,
                                sample_beacon_state_params,
                                keymap,
                                pubkeys,
                                deposit_contract_tree_depth,
                                deposit_index,
                                success):
    validator_index = 0
    withdrawal_credentials = b'\x34' * 32
    state, deposit = create_mock_deposit(
        config,
        sample_beacon_state_params,
        keymap,
        pubkeys,
        withdrawal_credentials,
        validator_index,
    )
    deposit = deposit.copy(
        index=deposit_index,
    )

    if success:
        validate_deposit_proof(state, deposit, deposit_contract_tree_depth)
    else:
        with pytest.raises(ValidationError):
            validate_deposit_proof(state, deposit, deposit_contract_tree_depth)


def test_process_deposit(config,
                         sample_beacon_state_params,
                         keymap,
                         pubkeys):
    validator_index = 0
    withdrawal_credentials = b'\x34' * 32
    state, deposit = create_mock_deposit(
        config,
        sample_beacon_state_params,
        keymap,
        pubkeys,
        withdrawal_credentials,
        validator_index,
    )

    # Add the first validator
    result_state = process_deposit(
        state=state,
        deposit=deposit,
        config=config,
    )

    assert len(result_state.validators) == 1
    validator = result_state.validators[validator_index]
    assert validator.pubkey == pubkeys[validator_index]
    assert validator.withdrawal_credentials == withdrawal_credentials
    assert result_state.balances[validator_index] == config.MAX_EFFECTIVE_BALANCE
    # test immutable
    assert len(state.validators) == 0
