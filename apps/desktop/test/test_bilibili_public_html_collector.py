import json,sys,tempfile,unittest,urllib.error,urllib.request,os,time,subprocess,ssl
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'apps/desktop'))
import bilibili_public_html_collector as html
from bilibili_html_adapter import classify_video,InvalidPublicVideo
from collector_worker import run_selected_collector,build_script_args,collect_output_contract,file_state

A='BV1234567890';B='BV0987654321';C='BV0123456789'
def body(bvid,*,child=None,title='【MC整合包发布】星港2.0'):
 video={'bvid':bvid,'state':0,'title':title,'owner':{'name':'fixture'},'pubdate':1790502559,'duration':80,'desc':'下载说明见主页动态','stat':{'view':10}}
 if child:video['ugc_season']={'sections':[{'episodes':[{'bvid':child}]}]}
 return '<script>window.__INITIAL_STATE__='+json.dumps({'bvid':bvid,'videoData':video,'tags':[{'tag_name':'我的世界'}]},ensure_ascii=False)+'; throw new Error("must never execute");</script>'

def unavailable_body(bvid):
 return '<title>视频去哪了呢？_哔哩哔哩_bilibili</title><script>window.__INITIAL_STATE__='+json.dumps({'bvid':bvid,'error':{'code':404,'trueCode':-404},'videoData':{'stat':{},'owner':{}}})+';</script>'

def invisible_body(bvid,code=62002,message='稿件不可见',canonical=None):
  return '<title>视频去哪了呢？_哔哩哔哩_bilibili</title><meta property="og:url" content="'+(canonical or f'https://www.bilibili.com/video/{bvid}/')+'"><script>window.__INITIAL_STATE__='+json.dumps({'bvid':bvid,'error':{'code':404,'trueCode':code,'message':message},'videoData':{'stat':{},'owner':{}}})+';</script>'

def owner_only_body(bvid):
 return '<title>视频去哪了呢？_哔哩哔哩_bilibili</title><meta property="og:url" content="https://www.bilibili.com/video/'+bvid+'/"><div class="error-prompt"><div class="error-text">当前稿件up主设置为仅自见</div></div><script>window.__INITIAL_STATE__='+json.dumps({'bvid':bvid,'error':{'code':404,'trueCode':62012,'message':'62012','fromSpider':False},'videoData':{'stat':{},'owner':{}}})+';</script>'

class Transport:
 def __init__(self,pages=None,denied=False):self.pages=pages or {};self.requests=[];self.denied=denied
 def fetch(self,url,limit):
  self.requests.append(url)
  if url.endswith('/robots.txt'):return 'User-agent: *\nDisallow: /\n' if 'www.' not in url or self.denied else 'User-agent: *\nDisallow: /medialist/detail/\n'
  ident=url.split('/')[-2];value=self.pages[ident]
  if isinstance(value,Exception):raise value
  return value

class Tests(unittest.TestCase):
 def test_owner_only_video_retains_old_record_and_continues_public_queue(self):
  with tempfile.TemporaryDirectory() as d:
   old=[{'bvid':A,'desc':'private video old evidence','pub_timestamp':20},{'bvid':B,'pub_timestamp':10}]
   r,rows=self.run_collect(d,old,Transport({A:owner_only_body(A),B:body(B)}),mode='catalog',limit=2)
   self.assertEqual(rows[0],old[0]);self.assertEqual(r['details']['observedCount'],1);self.assertIsNone(r['details']['stopped'])
   state=json.loads((Path(d)/'state.json').read_text());self.assertEqual(state['unavailable'][A]['initialStateTrueCode'],62012)
   self.assertEqual(state['days'][html.utc()[:10]],[A,B])

 def test_owner_only_detection_requires_all_rendered_identity_signals(self):
  sample=owner_only_body(A)
  for value in [sample.replace('当前稿件up主设置为仅自见','请先登录'),sample.replace('62012','62004'),sample.replace('"fromSpider": false','"fromSpider": true'),sample.replace('video/'+A,'video/'+B),sample.replace('<div class="error-text">当前稿件up主设置为仅自见</div>','<!-- 当前稿件up主设置为仅自见 -->'),sample.replace('"bvid": "'+A+'"','"bvid": "'+B+'"')]:
   with self.subTest(value=value):
    with self.assertRaises(InvalidPublicVideo) as caught:html.parse_public_video(value,A)
    self.assertIs(type(caught.exception),InvalidPublicVideo)

 def test_certificate_stop_never_resumes_as_tls_eof_after_cooldown(self):
  with tempfile.TemporaryDirectory() as d:
   old=[{'bvid':A,'pub_timestamp':20},{'bvid':B,'pub_timestamp':10}]
   cert=urllib.error.URLError(ssl.SSLCertVerificationError(1,'certificate verify failed'))
   with patch.object(html,'utc',return_value='2026-10-06T08:00:00Z'):self.run_collect(d,old,Transport({A:cert}),mode='catalog',limit=2)
   p=Path(d)/'state.json';prior=json.loads(p.read_text());t=Transport({B:body(B)})
   with patch.object(html,'utc',return_value='2026-10-06T08:10:00Z'),patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'result2.json')}):html.collect(d,p,mode='catalog',limit=2,transport=t)
   self.assertEqual(t.requests,[]);self.assertEqual(json.loads(p.read_text())['stopped'],prior['stopped'])

 def test_old_mislabelled_certificate_stop_is_not_resumed(self):
  with tempfile.TemporaryDirectory() as d:
   self.setup_input(d,[{'bvid':A},{'bvid':B}]);p=Path(d)/'state.json'
   stop={'at':'2026-10-06T08:00:00Z','bvid':A,'httpStatus':None,'error':'<urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed>','stopKind':'transport','reason':'tls-eof-unverified','stage':'video'}
   prior={'schema':1,'days':{'2026-10-06':[A]},'stopped':stop};p.write_text(json.dumps(prior));t=Transport({B:body(B)})
   with patch.object(html,'utc',return_value='2026-10-06T08:10:00Z'),patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'result.json')}):html.collect(d,p,mode='catalog',transport=t)
   self.assertEqual(t.requests,[]);self.assertEqual(json.loads(p.read_text()),prior)

 def test_robots_tls_interruption_can_be_rechecked_on_next_update_after_cooldown(self):
  class Interrupted(Transport):
   def fetch(self,url,limit):
    self.requests.append(url);raise urllib.error.URLError(ssl.SSLEOFError(8,'EOF occurred in violation of protocol'))
  with tempfile.TemporaryDirectory() as d:
   old=[{'bvid':A,'desc':'preserve'}]
   with patch.object(html,'utc',return_value='2026-10-06T08:00:00Z'):first,_=self.run_collect(d,old,Interrupted(),mode='catalog')
   state_path=Path(d)/'state.json';prior=json.loads(state_path.read_text());self.assertEqual(prior['stopped']['stopKind'],'transport');self.assertEqual(prior['stopped']['stage'],'robots')
   t=Transport({A:body(A)})
   with patch.object(html,'utc',return_value='2026-10-06T08:01:00Z'),patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'r2.json')}):html.collect(d,state_path,mode='catalog',transport=t)
   self.assertEqual(t.requests,[]);self.assertEqual(json.loads(state_path.read_text())['stopped'],prior['stopped'])
   with patch.object(html,'utc',return_value='2026-10-06T08:10:00Z'),patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'r3.json')}):result=html.collect(d,state_path,mode='catalog',transport=t)
   self.assertEqual(result['details']['observedCount'],1);state=json.loads(state_path.read_text());self.assertEqual(state['stopHistory'][0]['stopped'],prior['stopped']);self.assertIsNone(state['stopped'])

 def test_exact_legacy_robots_tls_stop_keeps_history_and_skips_attempted_video(self):
  with tempfile.TemporaryDirectory() as d:
   self.setup_input(d,[{'bvid':A},{'bvid':B}]);p=Path(d)/'state.json'
   prior={'schema':1,'days':{'2026-10-06':[A]},'stopHistory':[{'old':'retained'}],'stopped':{'at':'2026-10-06T07:00:00Z','httpStatus':None,'error':'<urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1082)>'}};p.write_text(json.dumps(prior));t=Transport({B:body(B)})
   with patch.object(html,'utc',return_value='2026-10-06T08:00:00Z'),patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'result.json')}):r=html.collect(d,p,mode='catalog',transport=t)
   self.assertEqual(r['details']['observedCount'],1);after=json.loads(p.read_text());self.assertEqual(after['stopHistory'][0],prior['stopHistory'][0]);self.assertEqual(after['stopHistory'][1]['stopped'],prior['stopped']);self.assertEqual(after['days']['2026-10-06'],[A,B]);self.assertFalse(any('/'+A+'/' in u for u in t.requests))

 def test_catalog_batch_limit_does_not_claim_complete_known_catalog(self):
  with tempfile.TemporaryDirectory() as d:
   r,_=self.run_collect(d,[{'bvid':A},{'bvid':B}],Transport({A:body(A)}),mode='catalog',limit=1)
   self.assertFalse(r['details']['knownCatalogCompleted']);self.assertEqual(r['details']['unverifiedQueuedCount'],1)
 def test_tls_eof_defers_only_that_video_and_does_not_claim_complete(self):
  with tempfile.TemporaryDirectory() as d:
   old=[{'bvid':A,'desc':'preserve','pub_timestamp':20},{'bvid':B,'pub_timestamp':10}]
   eof=urllib.error.URLError(ssl.SSLEOFError(8,'EOF occurred in violation of protocol'))
   r,rows=self.run_collect(d,old,Transport({A:eof,B:body(B)}),mode='catalog',limit=2)
   self.assertEqual(rows[0],old[0]);self.assertEqual(r['details']['observedCount'],1)
   self.assertIsNone(r['details']['stopped']);self.assertFalse(r['details']['knownCatalogCompleted'])
   state=json.loads((Path(d)/'state.json').read_text());self.assertIn(A,state['transportFailures']);self.assertNotIn(A,state['unavailable'])
   self.assertEqual(r['details']['pendingTransportFailureCount'],1)
   again=Transport()
   with patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'result2.json')}):html.collect(d,Path(d)/'state.json',transport=again,mode='catalog')
   self.assertEqual(again.requests,[])
 def test_three_consecutive_tls_eof_errors_open_circuit_without_more_requests(self):
  with tempfile.TemporaryDirectory() as d:
   ids=[A,B,C,'BV9999999999'];eof=urllib.error.URLError(ssl.SSLEOFError(8,'EOF occurred in violation of protocol'))
   t=Transport({x:eof for x in ids})
   r,_=self.run_collect(d,[{'bvid':x,'pub_timestamp':100-i} for i,x in enumerate(ids)],t,mode='catalog',limit=4)
   self.assertEqual(sum('/video/' in x for x in t.requests),3)
   self.assertTrue(r['details']['stopped']['transportFailureCircuitOpen']);self.assertFalse(r['details']['knownCatalogCompleted'])
 def test_tls_certificate_errors_and_access_gates_still_stop_immediately(self):
  for error in (urllib.error.URLError(ssl.SSLCertVerificationError(1,'certificate verify failed')),urllib.error.HTTPError('https://www.bilibili.com/',429,'denied',{},None),ValueError('captcha fixture')):
   with self.subTest(error=error),tempfile.TemporaryDirectory() as d:
    t=Transport({A:error,B:body(B)})
    r,_=self.run_collect(d,[{'bvid':A,'pub_timestamp':20},{'bvid':B,'pub_timestamp':10}],t,mode='catalog',limit=2)
    self.assertIsNotNone(r['details']['stopped']);self.assertEqual(sum('/video/' in x for x in t.requests),1)
 def test_legacy_tls_eof_resolution_preserves_ledger_and_never_resolves_refusals(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'state.json';stop={'at':'2026-10-06T07:01:16Z','bvid':A,'error':'<urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1082)>','httpStatus':None}
   prior={'schema':1,'days':{'2026-10-06':[A]},'stopped':stop,'stopHistory':[{'older':'retained'}]};p.write_text(json.dumps(prior))
   html.resolve_transport_stop(p);state=json.loads(p.read_text())
   self.assertEqual(state['days'],prior['days']);self.assertEqual(state['stopHistory'][0],prior['stopHistory'][0]);self.assertEqual(state['stopHistory'][1]['stopped'],stop)
   self.assertIn(A,state['transportFailures']);self.assertIsNone(state['stopped']);self.assertEqual(state['transportFailureStreak'],1)
   for extra in ({'httpStatus':403},{'htmlEvidence':{}},{'transportFailureCircuitOpen':True},{'error':'captcha'},{'bvid':B}):
    p.write_text(json.dumps({**prior,'stopped':{**stop,**extra}}));before=p.read_bytes()
    with self.assertRaises(html.Refusal):html.resolve_transport_stop(p)
    self.assertEqual(p.read_bytes(),before)
 def test_evidenced_invisible_video_is_skipped_without_global_stop(self):
  with tempfile.TemporaryDirectory() as d:
   r,rows=self.run_collect(d,[{'bvid':A,'pub_timestamp':20},{'bvid':B,'pub_timestamp':10}],Transport({A:invisible_body(A),B:body(B)}),mode='catalog',limit=2)
   self.assertEqual(r['details']['observedCount'],1);self.assertIsNone(r['details']['stopped']);self.assertTrue(r['details']['knownCatalogCompleted']);self.assertEqual(len(rows),2)
   state=json.loads((Path(d)/'state.json').read_text());e=state['unavailable'][A]['htmlEvidence'];self.assertEqual(Path(e['path']).read_text(),invisible_body(A));self.assertEqual(state['unavailable'][A]['initialStateTrueCode'],62002)
 def test_invisible_classification_requires_exact_evidenced_code_message_and_identity(self):
  for value in [invisible_body(A,62004),invisible_body(A,message='登录后查看'),invisible_body(B),invisible_body(A,canonical=f'https://www.bilibili.com/video/{B}/'),invisible_body(A).replace('视频去哪了呢？','安全验证')]:
   with self.subTest(value=value):
    with self.assertRaises(InvalidPublicVideo) as caught:html.parse_public_video(value,A)
    self.assertIs(type(caught.exception),InvalidPublicVideo)
 def test_content_gate_requires_mc_pack_identity_and_rejects_keyword_bait(self):
  cases=[
   ('cs1.6血腥版自制整合包发布','下载地址 https://example.invalid/game.zip',False),
   ('cs1.6血腥版自制整合包发布','Minecraft Forge\n整合包名称：CS1.6\n游戏版本：1.20.1\n模组数量：100',False),
   ('新版Xash0.21 手机版cs1.6高仿steam端游整合包发布！及游戏数据包导入教程','Minecraft 我的世界标签不代表游戏包身份',False),
   ('我的世界光影整合包发布','Minecraft 1.20.1 光影集合',False),
   ('【我的世界】10款大型冒险向整合包推荐','这些都是MC整合包',False),
   ('【MC整合包发布】凡人修仙','整合👉https://b23.tv/%63%6D%2D%63%6D%74%2D%31',False),
   ('当你和大聪明朋友一起玩自制整合包2（挑战开挂不被发现）','我的世界整合包',False),
   ('【整合包发布】MC版GTA《烈阳调查局》0.2测试版','Minecraft 1.20.1 Forge，本整合包发布',True),
   ('【MC整合包发布】星港2.0','下载说明见主页动态',True),
   ('【整合包发布】一款深度魔改整合包—亚特兰深渊1.0正式版',
    'MC百科：https://www.mcmod.cn/modpack/735.html',True),
   ('【方块闲境】整合包发布！如果你喜欢星露谷，一定要来尝试',
    '模组数：187\n整合包：https://bbsmc.net/modpack/fkxj',True),
   ('【MC整合包发布】远梦之棺2.0',
    '三连后关注并私信“已三连”也无法获取！\nhttps://www.xyebbs.com/res-id/the-casket-of-reveries',True),
   ('【大型整合包发布】乌托邦探险之旅',
    '整合包名称：乌托邦探险之旅\n游戏版本：1.20.1\n整合包一共有276个模组。\n关注UP后，会自动私信发给你链接',True),
   ('[FCL]低配宝可梦整合包V0.1手机版发布+安装教程',
    '方可梦:轻行\n游戏版本1.21.1Fabric\n整合包版本V0.1\nMod 数量：100-',True),
   ('【森语田园】Minecraft 1.20.1定制养老地图整合包发布',
    '整合包包含多种农业、渔业、畜牧业和建筑类模组。',True),
   ('我的世界MC1.20.1整合包“重生”0.2测试版发布',
    'https://bbsmc.net/modpack/1.20.1-re/version/0.2',True),
   ('你还在为整合包内玩科技烦恼吗？【模组介绍：共振存储】',
    'MC百科：https://www.mcmod.cn/class/29199.html',False),
   ('自动化基地！我的世界机械动力自制整合包存档参观','乐乐乐',False),
   ('【我的世界】亡者世界6.0！攻略向整合包推荐！教程篇-新手入门指南',
    'https://www.curseforge.com/minecraft/modpacks/deceasedcraft',False),
   ('奥特100天整合包发布！一期视频教你玩懂【奥特宇宙100天模组攻略】',
    '游戏版本：1.21.1newforge\n本期带来模组的攻略视频',False),
   ('两个我的世界整合包介绍',
    'https://www.curseforge.com/minecraft/modpacks/deceasedcraft',False),
   ('MC整合包震撼不发布','Minecraft整合包',False),
   ('MC整合包正式版发布预热PV','https://bbsmc.net/modpack/example',False),
   ('奥特宇宙100天整合包0.8版本【强度信息统计表发布】',
    'Minecraft 1.21.1 Forge',False),
   ('MC整合包一键启动！新版发布1.21.1直装版','-',False),
   ('【MC整合包发布】洞穴之旅',
    '整合包包含120个模组，Minecraft 1.20.1 Forge。\n推荐服务器购买链接：https://example.invalid/hosting',True),
   ('最适合初次游玩铁砧工艺的整合包！【铁砧工艺极速版0.10.0发布！】',
    'https://www.mcmod.cn/modpack/123.html',True),
   ('【明日方舟 × Minecraft】大群方舟整合包-4.0更新演示',
    'https://www.curseforge.com/minecraft/modpacks/arknight',True),
   ('补档：[MC整合包杂谈]脆骨症2？别洗了',
    'https://www.curseforge.com/minecraft/modpacks/example',False),
   ('【MC】星空整合包介绍',
    '整合包原作者：@另一位作者\n原页：https://www.mcmod.cn/modpack/123.html',True),
   ('【MC】星空整合包实况介绍',
    '整合包原作者：@另一位作者\n原页：https://www.mcmod.cn/modpack/123.html',False),
   ('[MCMOD]科技进化整合包 现已推出抢先体验版!',
    'CurseForge: https://www.curseforge.com/minecraft/modpacks/minetech-evolution\nMC百科:https://www.mcmod.cn/modpack/924.html',True),
   ('[MCMOD]科技进化整合包 即将推出抢先体验版!',
    'https://www.curseforge.com/minecraft/modpacks/minetech-evolution',False),
   ('【MC 整合包发布】开普勒方舟计划 —— 突破引力的桎梏，开拓异星的序章',
    '作者：\n@xp不是小胖\n@滑稽且狗头13\n为瓦尔基里物理引擎预留6GB空余内存。',True),
   ('【MC 整合包实况】开普勒方舟计划',
    '作者：\n@xp不是小胖\n@滑稽且狗头13',False),
   ('更新整合包到最新版，结果我发现……【懒狗生存S2P27】ATM9 All the Mods 9',
    '整合包介绍：[ATM9]All the Mods 9\nhttps://www.mcmod.cn/modpack/623.html',False),
   ('【MC整合包发布】星港S2正式版介绍',
    'https://www.mcmod.cn/modpack/123.html',True),
   ('[MC整合包发布前预热]未尽之路涅槃',
    'https://bbsmc.net/modpack/unfinished_path_nirvana',False),
   ('【MC整合包发布】神秘回归前的预热「神秘启旅」',
    '游戏版本：1.20.1\n模组数量：264\n整合包版本：beta 0.9\nhttps://www.mcmod.cn/modpack/1232.html',True),
   ('【mc整合包】新包发布！新生活奇妙冒险日记，将会在三月底发布正式版',
    '整合包将会在三月中下旬发布首个版本并且发布玩法视频',False),
   ('【MC整合包发布】星港测试版，正式版下月发布',
    '现已提供测试版；整合包正式版将在下月发布。',True),
   ('最新【MC整合包发布】剑痕纪元0.9.71版本更新介绍，速来领取',
    '点头像进动态直接拿！\n记得三连！！',False),
   ('〖我的世界整合包〗宝可梦地平线2.0正式发布',
    '点头像去动态自己拿，记得彡莲哦！！',False),
   ('【MC整合包发布】星港',
    '点头像去动态自己拿，记得三连哦。\n整合包包含120个模组，Minecraft 1.20.1 Forge。',True),
   ('最新【Minecraft】我的世界网易基岩版更好的MC整合包？我的世界自制模组整合介绍不容错过',
    '',False),
   ('【我的世界】1.20.1机械动力种田女仆 懒人整合包分享',
    '非大型内容向，只是调好光影兼容的自用懒人包，也许有人需要就分享一下\n下载：https://pan.baidu.com/s/example',True),
   ('【MC整合包发布】不容错过的星港',
    'https://www.mcmod.cn/modpack/123.html',True),
  ]
  for title,desc,accepted in cases:
   with self.subTest(title=title):
    video={'title':title,'desc':desc,'owner':{'name':'fixture'},'duration':90}
    self.assertEqual(classify_video(video,['我的世界'])['accepted'],accepted)
 def setup_input(self,d,rows):
  p=Path(d)/'crawler_output/bilibili_modpacks.json';p.parent.mkdir(parents=True);p.write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8');return p
 def run_collect(self,d,rows,transport,**kw):
  raw=self.setup_input(d,rows);result=Path(d)/'build/result.json'
  with patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(result)}):r=html.collect(Path(d),Path(d)/'state.json',transport=transport,**kw)
  return r,json.loads(raw.read_text(encoding='utf-8'))
 def test_metadata_does_not_replace_full_auxiliary_content_or_versions(self):
  old={'bvid':A,'title':'old','desc':'full description','desc_observed':True,'desc_checked_at':'2026-09-28','pinned_comment':'old comment','pinned_comment_observed':True,'subtitle_observed':True,'subtitle_text':'old subtitle','all_versions':['1.20.1'],'pack_version':'3.4.5','download_links':[{'url':'https://example.invalid/old'}],'download_links_observed':True,'has_server':False}
  with tempfile.TemporaryDirectory() as d:
   r,rows=self.run_collect(d,[old],Transport({A:body(A)}),bvid=A,limit=1)
   for k in ('desc','desc_observed','desc_checked_at','pinned_comment','pinned_comment_observed','subtitle_observed','subtitle_text','all_versions','pack_version','download_links','download_links_observed','has_server'):self.assertEqual(rows[0][k],old[k],k)
   self.assertEqual(rows[0]['views'],10);self.assertIn('source_html_checked_at',rows[0]);self.assertEqual(r['status'],'partial');self.assertFalse(r['requestCompleted'])
 def test_new_mode_confirms_season_candidate_before_inserting_and_deduplicates(self):
  with tempfile.TemporaryDirectory() as d:
   t=Transport({A:body(A,child=B),B:body(B,child=B)})
   r,rows=self.run_collect(d,[{'bvid':A,'title':'known'}],t,mode='new',bvid=A,limit=3)
   self.assertEqual([v['bvid'] for v in rows],[A,B]);self.assertEqual(r['details']['newCount'],1)
   self.assertEqual(sum('/video/' in u for u in t.requests),2)
   self.assertEqual(rows[1]['pack_first_release_verified'],False);self.assertNotIn('desc',rows[1]);self.assertFalse(rows[1]['desc_observed']);self.assertIsNone(rows[1]['has_server'])
 def test_403_preserves_old_and_refusal_persists_without_second_request(self):
  for code in (403,412):
   with self.subTest(code=code),tempfile.TemporaryDirectory() as d:
    old=[{'bvid':A,'title':'old'}];t=Transport({A:urllib.error.HTTPError('https://www.bilibili.com/video/'+A+'/',code,'denied',{},None)})
    r,rows=self.run_collect(d,old,t,bvid=A,limit=1);self.assertEqual(rows,old);self.assertEqual(r['status'],'failed')
    ledger=Path(d)/'state.json';before=ledger.read_bytes()
    with self.assertRaises(html.Refusal):html.resolve_unavailable_stop(ledger,A,unavailable_body(A))
    self.assertEqual(ledger.read_bytes(),before)
    again=Transport({A:body(A)})
    with patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'result2.json')}):r2=html.collect(d,ledger,transport=again,bvid=A,limit=1)
    self.assertEqual(again.requests,[]);self.assertEqual(r2['status'],'failed');self.assertIn('Previous HTML refusal',r2['errors'][0])
 def test_unavailable_video_keeps_old_record_and_continues_next_candidate(self):
  with tempfile.TemporaryDirectory() as d:
   old=[{'bvid':A,'desc':'retain unavailable record','pub_timestamp':20},{'bvid':B,'pub_timestamp':10}]
   t=Transport({A:unavailable_body(A),B:body(B)})
   r,rows=self.run_collect(d,old,t,limit=2)
   self.assertEqual(rows[0],old[0]);self.assertEqual(r['details']['observedCount'],1);self.assertEqual(r['failedRequests'],1)
   self.assertIsNone(r['details']['stopped']);self.assertEqual(r['details']['knownUnavailableCount'],1)
   ledger=Path(d)/'state.json';state=json.loads(ledger.read_text());state['days']={};ledger.write_text(json.dumps(state))
   again=Transport({B:body(B)})
   with patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'result2.json')}):html.collect(d,ledger,transport=again,limit=1)
   self.assertFalse(any('/'+A+'/' in u for u in again.requests))
 def test_legacy_unavailable_stop_requires_evidence_and_preserves_history(self):
  with tempfile.TemporaryDirectory() as d:
   ledger=Path(d)/'state.json';stop={'at':'2026-10-03T07:52:29Z','bvid':A,'error':'Missing or error initial state','httpStatus':None}
   ledger.write_text(json.dumps({'schema':1,'days':{'2026-10-03':[A]},'stopped':stop}));before=ledger.read_bytes()
   with self.assertRaises(ValueError):html.resolve_unavailable_stop(ledger,A,body(A))
   self.assertEqual(ledger.read_bytes(),before)
   html.resolve_unavailable_stop(ledger,A,unavailable_body(A));state=json.loads(ledger.read_text())
   self.assertEqual(state['stopHistory'][0]['stopped'],stop);self.assertEqual(state['days'],{'2026-10-03':[A]});self.assertIsNone(state['stopped'])
   self.assertIn(A,state['unavailable']);self.assertFalse(ledger.with_suffix('.json.lock').exists())
 def test_robots_refusal_makes_zero_video_requests(self):
  with tempfile.TemporaryDirectory() as d:
   t=Transport(denied=True);r,rows=self.run_collect(d,[{'bvid':A}],t,bvid=A)
   self.assertEqual(r['status'],'failed');self.assertFalse(any('/video/' in u for u in t.requests));self.assertTrue(r['details']['stopped'])
 def test_verified_prefix_then_failure_is_partial_with_all_old_ids(self):
  with tempfile.TemporaryDirectory() as d:
   t=Transport({A:body(A,child=B),B:ValueError('captcha fixture')})
   r,rows=self.run_collect(d,[{'bvid':A},{'bvid':C,'desc':'retain'}],t,mode='new',bvid=A,limit=3)
   self.assertEqual(r['status'],'partial');self.assertEqual(r['failedRequests'],1);self.assertEqual({v['bvid'] for v in rows},{A,C});self.assertEqual(rows[1]['desc'],'retain')
 def test_catalog_mode_can_continue_past_default_daily_batch_without_resetting_ledger(self):
  with tempfile.TemporaryDirectory() as d:
   ids=[f'BV{i:010d}' for i in range(1,33)]
   self.setup_input(d,[{'bvid':v,'desc':'retain'} for v in ids])
   state=Path(d)/'state.json'; prior={'schema':1,'days':{html.utc()[:10]:ids[:30]},'stopped':None,'stopHistory':[{'evidence':'retained'}]};state.write_text(json.dumps(prior))
   t=Transport({v:body(v) for v in ids[30:]})
   with patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'result.json')}):r=html.collect(d,state,mode='catalog',limit=50,transport=t)
   self.assertEqual(r['details']['observedCount'],2)
   self.assertFalse(r['details']['fullRefresh'])
   self.assertEqual(r['details']['plannedCandidateCount'],2)
   self.assertTrue(r['details']['knownCatalogCompleted'])
   after=json.loads(state.read_text());self.assertEqual(after['days'][html.utc()[:10]],ids);self.assertEqual(after['stopHistory'],prior['stopHistory'])
   self.assertFalse(any('/'+v+'/' in u for v in ids[:30] for u in t.requests))
   self.assertIn('5000',build_script_args('bilibili',SimpleNamespace(limit=10000,mode='catalog',html_state=str(state),until=None)))
 def test_catalog_mode_never_bypasses_a_persisted_refusal(self):
  with tempfile.TemporaryDirectory() as d:
   self.setup_input(d,[{'bvid':A}])
   state=Path(d)/'state.json';prior={'schema':1,'days':{},'stopped':{'error':'HTTP 412','bvid':A},'stopHistory':[{'error':'older refusal'}]};state.write_text(json.dumps(prior));t=Transport()
   with patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'result.json')}):r=html.collect(d,state,mode='catalog',limit=5000,transport=t)
   self.assertEqual(t.requests,[]);self.assertEqual(json.loads(state.read_text()),prior);self.assertEqual(r['status'],'failed')
 def test_no_seed_or_duplicate_input_does_not_start_requests(self):
  for rows in ([],[{'bvid':A},{'bvid':A}]):
   with tempfile.TemporaryDirectory() as d:
    t=Transport();r,actual=self.run_collect(d,rows,t);self.assertEqual(actual,rows);self.assertEqual(t.requests,[]);self.assertEqual(r['status'],'failed')
 def test_daily_repeat_does_not_issue_content_or_robots_requests(self):
  with tempfile.TemporaryDirectory() as d:
   r,_=self.run_collect(d,[{'bvid':A}],Transport({A:body(A)}),bvid=A,limit=1)
   t=Transport()
   with patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'result2.json')}):r2=html.collect(d,Path(d)/'state.json',transport=t,bvid=A,limit=1)
   self.assertEqual(t.requests,[]);self.assertEqual(r2['status'],'failed')
 def test_next_isolated_job_skips_attempted_seeds_before_applying_limit(self):
  with tempfile.TemporaryDirectory() as d:
   self.setup_input(d,[{'bvid':A,'pub_timestamp':20},{'bvid':C,'pub_timestamp':10}])
   state=Path(d)/'state.json';state.write_text(json.dumps({'schema':1,'days':{html.utc()[:10]:[A]},'stopped':None}),encoding='utf-8')
   t=Transport({C:body(C)})
   with patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'result.json')}):r=html.collect(d,state,limit=1,transport=t)
   self.assertEqual(r['status'],'partial');self.assertEqual(r['details']['observations'][0]['bvid'],C)
   self.assertFalse(any('/'+A+'/' in u for u in t.requests))
 def test_unchanged_bytes_with_finite_observation_are_still_partial(self):
  with tempfile.TemporaryDirectory() as d:
   workspace=Path(d);raw=self.setup_input(d,[{'bvid':A}]);sidecar=workspace/'converted_output/data/bili_data.js';sidecar.parent.mkdir(parents=True);sidecar.write_text('window.biliModpacksData = '+raw.read_text(encoding='utf-8')+';',encoding='utf-8')
   before={'raw':file_state(raw),'sidecar':file_state(sidecar)};start=time.time_ns()-1_000_000_000
   for p in [raw,sidecar]:p.write_bytes(p.read_bytes())
   result=workspace/'build/desktop_collection_result.json';result.parent.mkdir();result.write_text(json.dumps({'platform':'bilibili','status':'partial','requestCompleted':False,'fetchedCount':1,'truncated':False,'details':{'coverage':'public-video-html-bounded'}}),encoding='utf-8')
   contract=collect_output_contract(workspace,'bilibili',start,before)
   self.assertFalse(contract['changed']);self.assertEqual(contract['outcome'],'partial_update')
 def test_response_gate_or_wrong_bvid_persists_without_insertion(self):
  for response in ('<title>安全验证</title>',body(B),unavailable_body(A).replace('视频去哪了呢？','安全验证'),unavailable_body(B)):
   with tempfile.TemporaryDirectory() as d:
    r,rows=self.run_collect(d,[{'bvid':A}],Transport({A:response}),bvid=A)
    self.assertEqual(rows,[{'bvid':A}]);self.assertEqual(r['status'],'failed');self.assertTrue(r['details']['stopped'])
 def test_worker_entry_outputs_partial_contract_and_snapshot_without_api_or_real_pointer(self):
  with tempfile.TemporaryDirectory() as d:
   workspace=Path(d)/'incoming/job';workspace.mkdir(parents=True)
   self.setup_input(workspace,[{'bvid':A,'desc':'retain full','desc_observed':True}])
   t=Transport({A:body(A)})
   class Response:
    def __init__(self,url):self.url=url;self.status=200;self.headers={};self.data=t.fetch(url,10**8).encode()
    def geturl(self):return self.url
    def read(self,n=-1):return self.data[:n] if n>=0 else self.data
    def __enter__(self):return self
    def __exit__(self,*a):return False
   class Opener:
    def open(self,request,timeout=None):
     assert 'Cookie' not in request.headers;return Response(request.full_url)
   args=SimpleNamespace(platform='bilibili',workspace=str(workspace),source_root=str(ROOT),limit=1,pages=50,until=None,mode='existing',bv=A,html_state=str(Path(d)/'collector-state/state.json'))
   self.assertIn('--html-state',build_script_args('bilibili',args));self.assertNotIn('sync-desc',build_script_args('bilibili',args))
   with patch.object(urllib.request,'build_opener',return_value=Opener()),patch('time.sleep',return_value=None):run_selected_collector(args)
   contract=json.loads((workspace/'build/desktop_update_result.json').read_text(encoding='utf-8'))
   self.assertEqual(contract['outcome'],'partial_update');self.assertTrue(contract['previousIdsPreserved']);self.assertEqual(contract['crawlerResult']['details']['observedCount'],1)
   self.assertTrue((workspace/'build/desktop_snapshot_manifest.json').exists());self.assertFalse((Path(d)/'active.json').exists())
   self.assertFalse(any('api.bilibili.com' in u and not u.endswith('/robots.txt') for u in t.requests))
 def test_saved_official_samples_parse_with_production_adapter(self):
  sample_dir=os.environ.get('MC_HTML_SAMPLE_DIR')
  if not sample_dir:
   self.skipTest('Set MC_HTML_SAMPLE_DIR to the separately transferred saved HTML fixtures')
  samples=Path(sample_dir)
  expected={'BV1NiKW6tErS':True,'BV17auR6GEWR':True}
  for bvid,accepted in expected.items():
   v,tags=html.parse_public_video((samples/(bvid+'.html')).read_text(encoding='utf-8'),bvid)
   self.assertEqual(classify_video(v,tags)['accepted'],accepted)
 def test_actual_worker_failure_is_utf8_and_reports_the_missing_seed_without_network(self):
  with tempfile.TemporaryDirectory() as d:
   r=subprocess.run([sys.executable,'-B',str(ROOT/'apps/desktop/collector_worker.py'),'--platform','bilibili','--workspace',str(Path(d)/'incoming/job'),'--source-root',str(ROOT),'--html-state',str(Path(d)/'state.json')],capture_output=True)
   self.assertEqual(r.returncode,1);text=r.stdout.decode('utf-8');r.stderr.decode('utf-8')
   self.assertIn('HTML局部更新未完成',text);self.assertIn('No known public BVID seed',text)
   contract=json.loads((Path(d)/'incoming/job/build/desktop_update_result.json').read_text(encoding='utf-8'))
   self.assertEqual(contract['outcome'],'failed');self.assertEqual(contract['crawlerResult']['details']['requests'],[])

if __name__=='__main__':unittest.main(verbosity=2)
