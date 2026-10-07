import unittest,ssl,urllib.error,sys,subprocess,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import public_api_transport as t
class Tests(unittest.TestCase):
 def setUp(self):t.SYSTEM_TLS_ORIGINS.clear()
 def test_public_api_uses_a_verified_context_with_available_trusted_roots(self):
  from unittest.mock import MagicMock
  response=MagicMock();response.__enter__.return_value=response
  response.read.return_value=b'[]'
  with patch.object(t.urllib.request,'urlopen',return_value=response) as request:
   self.assertEqual(t.read_public_api_json('https://api.bbsmc.net/v2/search',{}),[])
   context=request.call_args.kwargs.get('context')
   self.assertIsNotNone(context)
   self.assertEqual(context.verify_mode,ssl.CERT_REQUIRED)
   self.assertTrue(context.check_hostname)
   self.assertGreater(context.cert_store_stats()['x509_ca'],0)
 def test_eof_uses_same_origin_system_tls_without_disabling_certificate_checks(self):
  url='https://api.bbsmc.net/v2/project/XMUypeti/version'
  with patch.object(t.urllib.request,'urlopen',side_effect=urllib.error.URLError(ssl.SSLEOFError(8,'EOF'))),patch.object(t.subprocess,'run',return_value=subprocess.CompletedProcess([],0,b'[{"version_number":"0.3.0"}]\n__PUBLIC_STATUS__:200',b'')) as run:
   self.assertEqual(t.read_public_api_json(url,{'User-Agent':'fixture'})[0]['version_number'],'0.3.0')
   command=run.call_args.args[0];self.assertEqual(command[-1],url);self.assertNotIn('--insecure',command);self.assertNotIn('--location',command)
 def test_certificate_failure_and_access_denial_never_switch_transport(self):
  for error in [urllib.error.URLError(ssl.SSLCertVerificationError(1,'certificate failed')),urllib.error.HTTPError('u',403,'denied',{},None)]:
   with patch.object(t.urllib.request,'urlopen',side_effect=error),patch.object(t.subprocess,'run') as run:
    with self.assertRaises(urllib.error.URLError):t.read_public_api_json('https://api.bbsmc.net/v2/search',{})
    run.assert_not_called()
 def test_credentials_and_foreign_hosts_are_rejected_before_requests(self):
  for url,headers in [('https://evil.invalid/api',{}),('https://api.bbsmc.net/v2/search',{'Cookie':'secret'})]:
   with self.assertRaises(ValueError):t.read_public_api_json(url,headers)

class CollectorRefusal(unittest.TestCase):
 def test_existing_version_refresh_uses_verified_roots_too(self):
  import existing_version_crawler as collector
  from unittest.mock import MagicMock
  response=MagicMock();response.__enter__.return_value=response;response.status=200;response.read.return_value='[]'
  with patch.object(collector.urllib.request,'urlopen',return_value=response) as request:
   self.assertEqual(collector.request_json('https://api.modrinth.com/v2/project/fixture/version'),[])
   context=request.call_args.kwargs['context']
   self.assertEqual(context.verify_mode,ssl.CERT_REQUIRED)
   self.assertTrue(context.check_hostname)
 def test_both_collectors_stop_after_access_denial(self):
  import bbsmc_crawler,xyebbs_crawler
  for module,cls in [(bbsmc_crawler,bbsmc_crawler.BbsmcCrawler),(xyebbs_crawler,xyebbs_crawler.XyebbsCrawler)]:
   crawler=cls()
   with patch.object(module,'read_public_api_json',side_effect=urllib.error.HTTPError('u',429,'denied',{},None)) as request:
    self.assertIsNone(crawler._get_json('first'))
    self.assertIsNone(crawler._get_json('next'))
    self.assertEqual(request.call_count,1)
    self.assertEqual(crawler.stats['failed'],1)
