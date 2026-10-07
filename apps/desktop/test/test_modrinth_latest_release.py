import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import modrinth_crawler as crawler
class LatestRelease(unittest.TestCase):
 def test_both_search_and_versions_use_trusted_verified_contexts(self):
  import ssl
  from unittest.mock import MagicMock,patch
  response=MagicMock();response.__enter__.return_value=response;response.status=200
  response.read.side_effect=[b'{"hits":[],"total_hits":0}',b'[]']
  crawler.SOURCE_STOPPED=False
  with patch.object(crawler.urllib.request,'urlopen',return_value=response) as request:
   crawler.fetch_page(0);crawler.fetch_versions(['v1'])
   self.assertEqual(request.call_count,2)
   for call in request.call_args_list:
    context=call.kwargs.get('context')
    self.assertIsNotNone(context)
    self.assertEqual(context.verify_mode,ssl.CERT_REQUIRED)
    self.assertTrue(context.check_hostname)
    self.assertGreater(context.cert_store_stats()['x509_ca'],0)
 def test_catalog_resolves_latest_release_id_to_pack_version_not_game_version(self):
  item={'project_id':'project1','title':'星港','latest_version':'release1','versions':['1.20.1']}
  release={'id':'release1','project_id':'project1','version_number':'0.3.0','date_published':'2026-09-30','files':[{'url':'https://cdn.modrinth.com/data/project1/versions/release1/pack.mrpack'}]}
  row=crawler.standardize_pack(item,{release['id']:release})
  self.assertEqual(row['latest_version'],'0.3.0');self.assertEqual(row['releases'][0]['id'],'release1');self.assertEqual(row['mc_version'],'1.20.1')
 def test_other_project_release_is_not_attached(self):
  row=crawler.standardize_pack({'project_id':'project1','latest_version':'release1'},{'release1':{'id':'release1','project_id':'other','version_number':'9.9'}})
  self.assertNotIn('latest_version',row)

class SourceRefusal(unittest.TestCase):
 def test_search_denial_does_not_retry_or_request_release_endpoint(self):
  import urllib.error
  from unittest.mock import patch
  crawler.SOURCE_STOPPED=False
  try:
   with patch.object(crawler.urllib.request,'urlopen',side_effect=urllib.error.HTTPError('u',429,'refused',{},None)) as request,patch.object(crawler.time,'sleep'):
    self.assertIsNone(crawler.fetch_page(0))
    self.assertEqual(crawler.fetch_versions(['release1']),{})
    self.assertEqual(request.call_count,1)
  finally:crawler.SOURCE_STOPPED=False


class MissingLatestRelease(unittest.TestCase):
 def test_missing_one_release_keeps_other_verified_release(self):
  from unittest.mock import patch,MagicMock
  response=MagicMock();response.__enter__.return_value=response
  response.read.return_value=b'[{"id":"good","project_id":"p","version_number":"0.3.0"}]'
  crawler.SOURCE_STOPPED=False
  with patch.object(crawler.urllib.request,'urlopen',return_value=response):
   self.assertIn('good',crawler.fetch_versions(['good','deleted']))

if __name__=='__main__':unittest.main()
