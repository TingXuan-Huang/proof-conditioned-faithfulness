# Emitted JSON Schemas

These files are deterministic structural schemas emitted from the Pydantic models in
`src/proof_faithfulness/schema.py`. They support editor tooling and reject wrong field
types, missing fields, unknown fields, and representable scalar constraints.

The Pydantic models are the authoritative validators. JSON Schema cannot express all of
the cross-field rules enforced there, including dependency-graph acyclicity, exact
agreement between predecessor lists and edge lists, A/B signature distinctness, frozen
pilot reference approval, request-ID recomputation, or chronological consistency. Code
that accepts benchmark or run data must call `model_validate`; validating only against
these emitted files is insufficient.

Run `uv run proof-faithfulness schema export --output-dir schemas --force` after an
intentional contract change. `tests/unit/test_schema_exports.py` fails when checked-in
schemas are stale.
