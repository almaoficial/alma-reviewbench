"""Reviewer v2.3.2 fix tests: the reviewer's own gate resolver
learns "v141".

Source: DIAGNOSTICO-PRACTICA-ALMA-310-20261022.md — ALMA practice
run #310 died at run-agent admission with zero model calls: the
image carries TWO resolvers of RB_CONFIG_GATE that drifted apart.
agent/main.py's selector has admitted "v141" since the 1.4.1 gate
landed (paper Adenda 1) and did select it (the run header declared
validator=alma-evidence-gate/1.4.1, policy_sha256=73a403d8…), but
the reviewer-internal resolver, ``_resolve_gate_v23`` in
agent/llm_reviewer_v23.py, kept its own admission list ending at
"v14" and refused "v141" fail-closed before the selection prompt
was even built.  The base run #298 passed on the same image
because gate=v13 is present in both resolvers; #310 was the first
run to present "v141" to the reviewer's resolver.

The fix (paper Adenda 4), one branch and nothing else:

- ``_resolve_gate_v23`` gains the mirror branch: gate=v141
  resolves to (KNOWN_CLAIM_TYPES_V13, _CLASS_GUIDANCE_V13,
  GATE_V141_VERSION) — the 1.3.0's 19 classes and guidance, which
  the 1.4.1 inherits through the 1.4.0, with the 1.4.1's policy
  version as the identity.  The refusal message lists 'v141'.

Everything runs on scripted transports: no real model call, US$0.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from agent.alma_gate_v13 import (  # noqa: E402
    KNOWN_CLAIM_TYPES_V13,
    POLICY_VERSION as GATE_V13_VERSION,
)
from agent.alma_gate_v14 import POLICY_VERSION as GATE_V14_VERSION  # noqa: E402
from agent.alma_gate_v141 import POLICY_VERSION as GATE_V141_VERSION  # noqa: E402
from agent.llm_reviewer import RealLLMRefused  # noqa: E402
from agent.llm_reviewer_v23 import (  # noqa: E402
    _CLASS_GUIDANCE_V13,
    REVIEWER_VERSION,
    LLMReviewerV23,
    _resolve_gate_v23,
)
from test_llm_reviewer_v23 import (  # noqa: E402
    CONFIG_ALMA_V14,
    GeneralizedTransport,
    armed_env,
)

CONFIG_ALMA_V141 = dict(CONFIG_ALMA_V14, gate="v141")


class GateV141ResolutionTests(unittest.TestCase):
    """The combination no test covered: reviewer v2.3 x gate v141."""

    def test_v141_resolves_to_v13_classes_with_the_141_identity(self):
        claim_types, guidance, version = _resolve_gate_v23({"gate": "v141"})
        self.assertEqual(claim_types, KNOWN_CLAIM_TYPES_V13)
        self.assertEqual(len(claim_types), 19)
        self.assertIs(guidance, _CLASS_GUIDANCE_V13)
        self.assertEqual(version, GATE_V141_VERSION)
        self.assertEqual(version, "alma-evidence-gate/1.4.1")

    def test_v13_and_v14_still_resolve_as_before(self):
        claim_types, guidance, version = _resolve_gate_v23({"gate": "v13"})
        self.assertEqual(claim_types, KNOWN_CLAIM_TYPES_V13)
        self.assertIs(guidance, _CLASS_GUIDANCE_V13)
        self.assertEqual(version, GATE_V13_VERSION)
        claim_types, guidance, version = _resolve_gate_v23({"gate": "v14"})
        self.assertEqual(claim_types, KNOWN_CLAIM_TYPES_V13)
        self.assertIs(guidance, _CLASS_GUIDANCE_V13)
        self.assertEqual(version, GATE_V14_VERSION)

    def test_unknown_gate_still_refuses_and_the_message_lists_v141(self):
        with self.assertRaises(RealLLMRefused) as caught:
            _resolve_gate_v23({"gate": "v9"})
        self.assertIn("'v141'", str(caught.exception))
        self.assertIn("no model call was made", str(caught.exception))

    def test_reviewer_builds_with_the_v141_alma_config(self):
        reviewer = LLMReviewerV23.from_env(
            armed_env(), CONFIG_ALMA_V141, transport=GeneralizedTransport()
        )
        self.assertEqual(len(reviewer.claim_types), 19)
        self.assertEqual(reviewer.gate_version, "alma-evidence-gate/1.4.1")
        self.assertEqual(REVIEWER_VERSION, "llm-reviewer/2.3.2")


if __name__ == "__main__":
    unittest.main()
