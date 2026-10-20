# Explainable Recommendation Engine

## Objective and classification

Staywise ranks rooms against an authenticated customer's saved preferences. It is a **deterministic weighted content-based recommender**, not a trained machine-learning model: there is no training dataset, learned parameter, prediction target, or model fitting step.

Implementation: `recommendations/services.py`. Preferences are stored by `recommendations.models.UserPreference`; rooms, hotels, and amenities come from `hotels.models`.

## Inputs and hard constraints

The preference inputs are destination, room type, maximum nightly price, guests, requested dates, and amenities. Before scoring, `eligible_rooms()` retains only rooms that:

1. have `status="available"`;
2. have `capacity >= guests`; and
3. have no confirmed booking where `booking.check_in < requested_check_out` and `booking.check_out > requested_check_in`.

Capacity and date availability are therefore eligibility rules, not merely ranking hints. The configured budget is a soft preference: rooms up to 150% of budget can receive a declining score, and rooms further above budget receive zero budget points but can remain eligible.

## Feature normalization

Every raw feature score is in `[0, 1]`:

| Feature | Normalization |
| --- | --- |
| Budget | `1` at or below budget; above budget, `max(0, 1 - (price-budget)/(0.5×budget))`; `0.5` when no budget is supplied. |
| Location | `1` when the preferred text occurs case-insensitively in hotel city/country; `0` for a specified non-match; `0.5` when unspecified. |
| Room type | `1` for an exact selected type; `0` for a specified non-match; `0.5` when unspecified. |
| Amenities | selected amenity IDs offered by room or hotel divided by selected amenity count; `0.5` when none are selected. |
| Capacity | `min(room.capacity / guests, 1)` after the hard capacity filter. This is normally `1` for eligible rooms. |

Missing optional preferences use a neutral score rather than automatically rewarding or excluding a room. Guests default to two and are validated to at least one.

## Weights and formula

The configured values in `staywise/settings.py` are:

| Feature | Weight |
| --- | ---: |
| Budget | 30% |
| Location | 20% |
| Room type | 20% |
| Amenities | 20% |
| Capacity | 10% |

`get_weights()` clamps negative configured values to zero and normalizes the remaining values to sum to one. If the configured total is zero, it returns the default weights.

For normalized feature scores `s_i` and normalized weights `w_i`:

`final score = round(Σ(round(s_i × w_i × 100, 1)), 1)`

The service retains each raw percentage, weight percentage, and point contribution in `breakdown`. This small per-feature rounding means the implementation formula is the sum of rounded one-decimal contributions.

## Worked example

Consider an eligible two-person suite priced at `$125`, with a `$100` maximum budget, the requested destination and room type, and two of four selected amenities:

- Budget: price is halfway between `$100` and `$150`, so raw score `0.5`; contribution `0.5 × 0.30 × 100 = 15`.
- Location: match `1.0`; contribution `20`.
- Room type: match `1.0`; contribution `20`.
- Amenities: `2/4 = 0.5`; contribution `10`.
- Capacity: `min(2/2, 1) = 1`; contribution `10`.

Final score: `15 + 20 + 20 + 10 + 10 = 75.0%`.

This is a formula demonstration, not a recorded evaluation case.

## Explanations, missing preferences, and ties

`score_room()` generates up to four plain-language reasons for budget, destination, room type, amenities, capacity, and requested-date availability. With all optional preferences empty, it explains that capacity is satisfied and that ranking is consistent by price.

`recommendations_for()` sorts by:

1. score descending;
2. nightly price ascending; and
3. room primary key ascending.

This makes ties deterministic. If no room survives the hard constraints, the result is an empty list and the template displays an empty state.

## Evaluation

Run:

```bash
python manage.py evaluate_recommender
```

`evaluate_profiles()` reports the top room IDs and scores for each profile plus catalogue coverage: unique rooms returned across all top-k lists divided by available-room count. It does **not** measure relevance, accuracy, precision, recall, click-through rate, or customer satisfaction.

Observed on 2026-10-20 against the current development database:

- profile source: saved preferences;
- profiles evaluated: `2`;
- top-three rooms returned per profile: `3`;
- catalogue coverage: `1.0`;
- top scores: profile one `[65.0, 45.0, 45.0]`; profile two `[55.0, 55.0, 55.0]`.

These results depend on current local database contents and will change when profiles or rooms change.

## Limitations and improvements

- Exact/case-substring category matching cannot model nuanced similarity.
- Every selected amenity has equal importance.
- Capacity contributes little discrimination after being enforced as a hard constraint.
- The budget rule is soft and permits over-budget rooms.
- No behavioral history, collaborative signals, diversity control, or learned feedback exists.
- Coverage is not a relevance evaluation.

Future work should collect consented relevance judgements, define offline relevance metrics, allow amenity importance, measure diversity, test alternative budget policies, and only introduce a trained ranker if a suitable dataset and evaluation protocol exist.
