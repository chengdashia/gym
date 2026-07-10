from decimal import Decimal
from types import SimpleNamespace

from app.services.training_history import completed_set_values


def test_completed_set_values_use_actual_values_by_set_index():
    exercise = SimpleNamespace(sets=[
        SimpleNamespace(set_index=1, actual_reps=10, actual_weight_kg=Decimal("60"), completed=1),
        SimpleNamespace(set_index=2, actual_reps=8, actual_weight_kg=Decimal("60"), completed=1),
        SimpleNamespace(set_index=3, actual_reps=7, actual_weight_kg=Decimal("60"), completed=0),
    ])

    assert completed_set_values(exercise) == {
        1: (10, Decimal("60")),
        2: (8, Decimal("60")),
    }
