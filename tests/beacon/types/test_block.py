from eth.beacon.types.blocks import (
    BaseBeaconBlock,
)
from eth.beacon.types.attestations import (
    Attestation,
)


def test_defaults(sample_beacon_block_params):
    block = BaseBeaconBlock(**sample_beacon_block_params)
    assert block.slot == sample_beacon_block_params['slot']


def test_update_attestations(sample_attestation_params, sample_beacon_block_params):
    block = BaseBeaconBlock(**sample_beacon_block_params)
    attestations = block.body.attestations
    attestations = list(attestations)
    attestations.append(Attestation(**sample_attestation_params))
    body2 = block.body.copy(
        attestations=attestations
    )
    block2 = block.copy(
        body=body2
    )
    assert block2.num_attestations == 1
