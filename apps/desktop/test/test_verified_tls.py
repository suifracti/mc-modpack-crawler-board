import ssl
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import verified_tls


class Context:
 def __init__(self,roots):self.roots=roots;self.verify_mode=ssl.CERT_REQUIRED;self.check_hostname=True
 def cert_store_stats(self):return {'x509_ca':self.roots}


class VerifiedTlsTests(unittest.TestCase):
 def test_existing_system_context_is_kept_when_it_has_trusted_roots(self):
  existing=Context(128);calls=[]
  def factory(**kwargs):calls.append(kwargs);return existing
  result=verified_tls.create_verified_context(context_factory=factory,ca_paths=[])
  self.assertIs(result,existing);self.assertEqual(calls,[{}])

 def test_empty_default_store_falls_back_to_a_system_ca_bundle_without_disabling_verification(self):
  with tempfile.TemporaryDirectory() as d:
   ca=Path(d)/'system-ca.pem';ca.write_text('fixture public roots')
   calls=[]
   def factory(**kwargs):
    calls.append(kwargs);return Context(0 if 'cafile' not in kwargs else 7)
   result=verified_tls.create_verified_context(context_factory=factory,ca_paths=[ca])
   self.assertEqual(calls,[{}, {'cafile':str(ca)}]);self.assertEqual(result.cert_store_stats()['x509_ca'],7)
   self.assertEqual(result.verify_mode,ssl.CERT_REQUIRED);self.assertTrue(result.check_hostname)

 def test_missing_trusted_roots_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   def factory(**kwargs):return Context(0)
   with self.assertRaises(ssl.SSLError):verified_tls.create_verified_context(context_factory=factory,ca_paths=[Path(d)/'missing.pem'])


if __name__=='__main__':unittest.main()
