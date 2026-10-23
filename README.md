# DisputeArbiter

A two-party dispute arbiter for GenLayer Studionet. Two parties each file their side of a dispute in plain text, and validators read both sides against the agreed terms and rule who is right.

## Why evidence is bound to the sender

Each party's argument can only come from that party's own wallet. The contract takes no "party" argument: it reads the sender's address and files the evidence under the matching side. Each side can file once, and nobody can overwrite the other side's argument.

## Stages

```
OPEN  ->  READY  ->  RULED
```

- **OPEN:** waiting for evidence. Party A and Party B each file once with `submit_evidence`.
- **READY:** both sides are on record. Evidence is now closed.
- **RULED:** validators have ruled. The ruling is final and can't be requested again.

## Methods

| Method | Who | When |
| --- | --- | --- |
| `submit_evidence(evidence)` | party A or party B | stage is OPEN, and that side hasn't filed yet |
| `resolve_dispute()` | party A or party B | stage is READY |
| `get_dispute()` | anyone | any time |

## Validator ruling

Validators receive the agreed terms and both pieces of evidence. They must agree on the winner (`party_a` or `party_b`). The reasoning text can differ between validators. The rule is set with `gl.eq_principle.prompt_comparative`.

## Deploy

Deploy with three fields: `party_a` (wallet address), `party_b` (a different wallet address), and `terms` (the agreed terms, in plain text). The two parties must be different wallets.

## Tests

`python test_dispute_arbiter.py` runs 8 tests on the sender binding, the one-time filing rule, the stage checks and the ruling rule. GenLayer's runtime is stubbed, so these tests check plain-code logic, not live consensus.

## Limits

- Tested on Studionet only, not on public testnets.
- The contract doesn't hold GEN. It records a ruling, and doesn't move money.
- The terms are fixed at deploy time. Changing them needs a new contract.
- Only the two named wallets can take part. There's no way to add a third party.
