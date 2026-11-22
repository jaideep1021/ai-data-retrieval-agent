"""Bounded historical subset matching; this does not classify nationality."""
from itertools import product


def matching_partitions(carriers, target_rows, target_seats):
    """Return every carrier partition satisfying the two reference totals.

    Values contain row count and seats. Keep multiple solutions rather than
    arbitrarily choosing one. A bound prevents exponential work on large groups.
    """
    if len(carriers) > 18:
        raise ValueError('Too many carriers for bounded subset enumeration')
    if target_rows < 0 or target_seats < 0:
        raise ValueError('Negative reference target')
    ids = sorted(carriers)
    solutions = []
    for bits in product([0, 1], repeat=len(ids)):
        count = sum(carriers[c][0] * bit for c, bit in zip(ids, bits))
        seats = sum(carriers[c][1] * bit for c, bit in zip(ids, bits))
        if count == target_rows and seats == target_seats:
            solutions.append(dict(zip(ids, bits)))
    return solutions
