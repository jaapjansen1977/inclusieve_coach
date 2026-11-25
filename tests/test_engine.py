import json
import unittest
from pathlib import Path
from engine import Turn, evidence, references, RUBRIC

SCRIPTS = json.loads(Path(__file__).with_name("scenarios.json").read_text(encoding="utf8"))


class FeedbackTest(unittest.TestCase):
    def test_scenarios(self):
        for script, expected in zip(SCRIPTS, ([[1,2],[2,3],[2,5]], [[],[],[]])):
            turns = [Turn(i,i*100,i*100+90,role,words) for i,(role,words) in enumerate(script,1)]
            for rule, ids in zip(RUBRIC["criteria"],expected):
                result = evidence(turns,rule,RUBRIC)
                self.assertEqual(result,ids)
                if result:
                    self.assertEqual(references(turns,result), [turns[i-1] for i in ids])

    def test_missing_reference(self):
        with self.assertRaises(ValueError):
            references([], [42])

    def test_proposal_is_not_agreement(self):
        turns = [Turn(1,0,100,"cliënt","Als ik drie oefeningen tegelijk krijg, vergeet ik de helft."),
                 Turn(2,100,200,"therapeut","Dan schrijven we ze op.")]
        self.assertEqual([evidence(turns,r,RUBRIC) for r in RUBRIC["criteria"]],[[],[1,2],[]])
