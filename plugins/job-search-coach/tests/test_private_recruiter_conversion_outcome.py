import copy, datetime as dt, json, subprocess, sys, tempfile, unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'scripts'))
from validate_private_recruiter_conversion_outcome import validate_outcome, load_outcome

FIXTURES=ROOT/'tests/fixtures/private-recruiter-conversion-outcome'
SCHEMA=ROOT/'schemas/private-recruiter-conversion-outcome-v1.schema.json'
class OutcomeContractTests(unittest.TestCase):
    def test_all_event_mappings_and_locales_are_valid(self):
        expected={'contact_received':'clarify_context_before_reply','reply_received':'clarify_context_before_reply','referral_received':'prepare_fact_checked_summary','screen_requested':'route_to_prepare-role-interviews','interview_requested':'route_to_prepare-role-interviews','stop_decision':'record_stop_decision'}
        seen={}
        for path in sorted(FIXTURES.glob('*.json')):
            item=load_outcome(path); self.assertEqual([],validate_outcome(item,today=dt.date(2026,8,9)),path.name); seen[item['event_type']]=item['next_safe_action']
        self.assertEqual(expected,seen)
        self.assertEqual({'en','es'},{load_outcome(p)['locale'] for p in FIXTURES.glob('*.json')})

    def test_cli_accepts_injected_as_of_date(self):
        from validate_private_recruiter_conversion_outcome import _cli
        self.assertEqual(0, _cli([str(FIXTURES/'reply-received-en.json'), '--as-of', '2026-08-09']))
    def test_cli_normalizes_missing_unknown_and_help(self):
        script = ROOT / 'scripts' / 'validate_private_recruiter_conversion_outcome.py'
        valid = FIXTURES / 'reply-received-en.json'
        missing = subprocess.run([sys.executable, '-B', str(script), '--as-of', '2026-08-09'], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 3)
        missing_as_of = subprocess.run([sys.executable, '-B', str(script), str(valid)], capture_output=True, text=True)
        self.assertEqual(missing_as_of.returncode, 3)
        unknown = subprocess.run([sys.executable, '-B', str(script), str(valid), '--as-of', '2026-08-09', '--unknown'], capture_output=True, text=True)
        self.assertEqual(unknown.returncode, 3)
        help_result = subprocess.run([sys.executable, '-B', str(script), '--help'], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
    def test_schema_dates_declare_format_date(self):
        schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
        self.assertEqual('date', schema['properties']['event_date']['format'])
    def test_loader_rejects_symlink_and_excessive_nesting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); target = root/'target.json'; link = root/'link.json'
            target.write_text((FIXTURES/'contact-received-en.json').read_text(), encoding='utf-8')
            link.symlink_to(target)
            from validate_private_recruiter_conversion_outcome import OutcomeLoadError
            with self.assertRaises(OutcomeLoadError): load_outcome(link)
            deep = root/'deep.json'; deep.write_text(json.dumps({'x': [[[[[[[[[[[[[1]]]]]]]]]]]]] }), encoding='utf-8')
            with self.assertRaises(OutcomeLoadError): load_outcome(deep)
    def test_invalid_real_and_future_dates_fail(self):
        item=load_outcome(FIXTURES/'contact-received-en.json')
        for value in ('2026-02-30','20260808','2026-08-10'):
            bad=copy.deepcopy(item); bad['event_date']=value
            self.assertTrue(validate_outcome(bad,today=dt.date(2026,8,9)),value)
    def test_closed_fields_and_required_source_version_facts(self):
        item=load_outcome(FIXTURES/'reply-received-en.json')
        for field in ('source_artifact_id','source_version','fact_ids'):
            bad=copy.deepcopy(item); bad.pop(field); self.assertTrue(validate_outcome(bad),field)
        bad=copy.deepcopy(item); bad['extra']='x'; self.assertTrue(validate_outcome(bad))
    def test_mixed_ids_and_wrong_action_fail(self):
        item=load_outcome(FIXTURES/'referral-received-es.json'); item['source_artifact_id']='C-101'; self.assertTrue(validate_outcome(item))
        item=load_outcome(FIXTURES/'referral-received-es.json'); item['fact_ids']=['F-101','C-201']; self.assertTrue(validate_outcome(item))
        item=load_outcome(FIXTURES/'screen-requested-en.json'); item['next_safe_action']='prepare_fact_checked_summary'; self.assertTrue(validate_outcome(item))
    def test_fact_id_objects_and_mixed_types_fail_without_crashing(self):
        item = load_outcome(FIXTURES/'contact-received-en.json')
        for value in ([{}], ['F-101', {}], [1], [None]):
            bad = copy.deepcopy(item); bad['fact_ids'] = value
            errors = validate_outcome(bad)
            self.assertTrue(errors, value)
    def test_forbidden_raw_identity_action_outcome_score_prose_fails(self):
        for text in ('raw recruiter reply','Company: Acme','send a message','guaranteed interview','score 99','email test@example.com'):
            item=load_outcome(FIXTURES/'contact-received-en.json'); item['source_version']=text
            self.assertTrue(validate_outcome(item),text)
    def test_delivery_is_immutable_and_no_candidate_identifier(self):
        item=load_outcome(FIXTURES/'stop-decision-en.json')
        for key,value in {'draft_only':False,'external_actions_authorized':True,'no_message_action':False,'no_calendar_action':False,'raw_event_retained':True,'local_save_mode':'enabled'}.items():
            bad=copy.deepcopy(item); bad['delivery'][key]=value; self.assertTrue(validate_outcome(bad),key)
        bad=copy.deepcopy(item); bad['candidate_id']='C-001'; self.assertTrue(validate_outcome(bad))

    def test_delivery_rejects_integer_boolean_coercion(self):
        item = load_outcome(FIXTURES/'stop-decision-en.json')
        for key, value in {'draft_only': 1, 'external_actions_authorized': 0,
                           'no_message_action': 0, 'no_calendar_action': 0,
                           'raw_event_retained': 0}.items():
            bad = copy.deepcopy(item); bad['delivery'][key] = value
            self.assertTrue(validate_outcome(bad), key)
if __name__=='__main__': unittest.main()
