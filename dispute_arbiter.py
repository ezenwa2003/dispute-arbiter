# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

import json
import typing


class DisputeArbiter(gl.Contract):
    """
    Two-party dispute arbitration. Each party's evidence is bound to the wallet
    that sends it: a party's argument can only come from that party's own
    address, and it can be filed only once. Nobody can overwrite the other side.

    Stages: OPEN (waiting for evidence) -> READY (both sides filed) -> RULED
    """

    party_a: Address
    party_b: Address
    terms: str
    evidence_a: str
    evidence_b: str
    stage: str
    winner: str
    reasoning: str

    def __init__(self, party_a: str, party_b: str, terms: str):
        if party_a.lower() == party_b.lower():
            raise gl.vm.UserError("[EXPECTED] The two parties must be different wallets")
        self.party_a = Address(party_a)
        self.party_b = Address(party_b)
        self.terms = terms
        self.evidence_a = ""
        self.evidence_b = ""
        self.stage = "OPEN"
        self.winner = ""
        self.reasoning = ""

    @gl.public.write
    def submit_evidence(self, evidence: str) -> str:
        """The sender decides which side this is. There is no party parameter."""
        if self.stage != "OPEN":
            raise gl.vm.UserError(f"[EXPECTED] Evidence is closed, the case is {self.stage}")
        sender = gl.message.sender_address.as_hex
        if not evidence.strip():
            raise gl.vm.UserError("[EXPECTED] Evidence cannot be empty")
        if sender == self.party_a.as_hex:
            if self.evidence_a:
                raise gl.vm.UserError("[EXPECTED] Party A has already filed evidence")
            self.evidence_a = evidence
        elif sender == self.party_b.as_hex:
            if self.evidence_b:
                raise gl.vm.UserError("[EXPECTED] Party B has already filed evidence")
            self.evidence_b = evidence
        else:
            raise gl.vm.UserError("[EXPECTED] Only a party to this dispute can file evidence")
        if self.evidence_a and self.evidence_b:
            self.stage = "READY"
        return "Evidence recorded"

    @gl.public.write
    def resolve_dispute(self) -> typing.Any:
        if self.stage == "RULED":
            raise gl.vm.UserError("[EXPECTED] This dispute has already been ruled")
        if self.stage != "READY":
            raise gl.vm.UserError("[EXPECTED] Both parties must file evidence first")
        sender = gl.message.sender_address.as_hex
        if sender != self.party_a.as_hex and sender != self.party_b.as_hex:
            raise gl.vm.UserError("[EXPECTED] Only a party to this dispute can request a ruling")

        terms = self.terms
        evidence_a = self.evidence_a
        evidence_b = self.evidence_b

        def nondet() -> str:
            task = f"""
You are a neutral arbiter resolving a dispute between two parties.

Agreed terms:
{terms}

Party A's evidence:
{evidence_a}

Party B's evidence:
{evidence_b}

Decide which party's position is best supported by the agreed terms and evidence.

Respond using ONLY the following JSON format:
{{
    "winner": str,     // exactly "party_a" or "party_b"
    "reasoning": str   // one or two short sentences explaining the ruling
}}
It is mandatory that you respond only using the JSON format above,
nothing else. Don't include any other words or characters,
your output must be only JSON without any formatting prefix or suffix.
This result should be perfectly parsable by a JSON parser without errors.
"""
            result = (
                gl.nondet.exec_prompt(task)
                .replace("```json", "")
                .replace("```", "")
            )
            return json.dumps(json.loads(result), sort_keys=True)

        result_str = gl.eq_principle.prompt_comparative(
            nondet,
            principle=(
                "The 'winner' field must be the same value (party_a or "
                "party_b). The 'reasoning' field may be worded differently "
                "as long as it justifies the same winner based on the "
                "terms and evidence provided."
            ),
        )
        result_json = json.loads(result_str)
        if result_json["winner"] not in ("party_a", "party_b"):
            raise gl.vm.UserError("[EXPECTED] Validators returned an invalid winner")
        self.winner = result_json["winner"]
        self.reasoning = result_json["reasoning"]
        self.stage = "RULED"
        return result_json

    @gl.public.view
    def get_dispute(self) -> dict:
        return {
            "party_a": self.party_a.as_hex,
            "party_b": self.party_b.as_hex,
            "terms": self.terms,
            "evidence_a": self.evidence_a,
            "evidence_b": self.evidence_b,
            "stage": self.stage,
            "winner": self.winner,
            "reasoning": self.reasoning,
        }
