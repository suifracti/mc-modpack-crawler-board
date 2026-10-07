import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from bbsmc_crawler import BbsmcCrawler
class ReleaseEnrichment(unittest.TestCase):
 def test_successful_response_populates_versions_and_download_links(self):
  project={'project_id':'fool','title':'愚者'}
  versions=[{'version_number':'0.3.0','date_published':'2026-09-30T00:00:00Z','files':[{'url':'https://pan.quark.cn/s/example','filename':'client.zip','size':0}]}]
  crawler=BbsmcCrawler()
  with patch.object(crawler,'fetch_project_versions',return_value=versions):crawler.enrich_project_downloads([project],1)
  self.assertEqual(project['versions_data'][0]['version_number'],'0.3.0')
  self.assertEqual(len(project['download_links']),1)
