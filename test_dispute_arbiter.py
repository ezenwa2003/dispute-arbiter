"""Tests for DisputeArbiter's sender binding and one-time evidence rules.
GenLayer's runtime is stubbed, so these check plain-code rules only.
Run with:  python test_dispute_arbiter.py"""
import importlib.util, pathlib, sys, types

HERE = pathlib.Path(__file__).parent
A, B, OUT = "0xAA", "0xBB", "0xCC"

class Addr(str):
    @property
    def as_hex(self): return str(self)

class UserError(Exception): pass

gl = types.SimpleNamespace(
    Contract=object,
    public=types.SimpleNamespace(write=lambda fn: fn, view=lambda fn: fn),
    vm=types.SimpleNamespace(UserError=UserError, Return=type("Return", (), {})),
    nondet=types.SimpleNamespace(exec_prompt=None),
    eq_principle=types.SimpleNamespace(prompt_comparative=None),
    message=types.SimpleNamespace(sender_address=None),
)
gl.public.write.payable = gl.public.write
mod = types.ModuleType("genlayer")
mod.gl, mod.u256, mod.Address = gl, int, Addr
sys.modules["genlayer"] = mod

spec = importlib.util.spec_from_file_location("da", HERE / "dispute_arbiter.py")
da = importlib.util.module_from_spec(spec)
spec.loader.exec_module(da)

def as_(who):
    gl.message.sender_address = Addr(who)

def fresh():
    return da.DisputeArbiter(A, B, "Build a site by Aug 1")

def raises(fn, fragment):
    try:
        fn()
    except UserError as e:
        assert fragment in str(e), str(e)
        return
    raise AssertionError("expected UserError containing " + repr(fragment))

def test_party_wallets_must_differ():
    raises(lambda: da.DisputeArbiter(A, A, "x"), "must be different")

def test_evidence_is_bound_to_the_sender():
    d = fresh()
    as_(A); d.submit_evidence("I delivered on time")
    assert d.evidence_a == "I delivered on time" and d.evidence_b == ""
    as_(B); d.submit_evidence("Missing the form")
    assert d.stage == "READY"

def test_outsider_cannot_file():
    d = fresh()
    as_(OUT); raises(lambda: d.submit_evidence("I am a party"), "Only a party")
    assert d.evidence_a == "" and d.evidence_b == ""

def test_no_overwrite_by_the_other_side():
    d = fresh()
    as_(A); d.submit_evidence("first")
    as_(A); raises(lambda: d.submit_evidence("second"), "already filed")
    assert d.evidence_a == "first"

def test_evidence_closes_once_ready():
    d = fresh()
    as_(A); d.submit_evidence("a")
    as_(B); d.submit_evidence("b")
    as_(A); raises(lambda: d.submit_evidence("late"), "closed")

def test_empty_evidence_refused():
    d = fresh()
    as_(A); raises(lambda: d.submit_evidence("   "), "cannot be empty")

def test_ruling_needs_both_sides_and_a_party():
    d = fresh()
    as_(A); d.submit_evidence("a")
    as_(A); raises(lambda: d.resolve_dispute(), "file evidence first")
    as_(B); d.submit_evidence("b")
    as_(OUT); raises(lambda: d.resolve_dispute(), "Only a party")

def test_ruling_is_recorded_once():
    d = fresh()
    as_(A); d.submit_evidence("a")
    as_(B); d.submit_evidence("b")
    gl.eq_principle.prompt_comparative = lambda fn, principle: '{"winner": "party_b", "reasoning": "x"}'
    as_(A); d.resolve_dispute()
    assert d.stage == "RULED" and d.winner == "party_b"
    raises(lambda: d.resolve_dispute(), "already been ruled")

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t(); print("PASS", t.__name__)
    print(len(tests), "tests passed")
