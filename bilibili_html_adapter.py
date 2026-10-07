"""Parse public video HTML offline and classify bounded metadata observations."""
import json,re,hashlib,unicodedata
from datetime import datetime,timezone,timedelta
from html.parser import HTMLParser
from pathlib import Path
from bilibili_html_extract import extract_modpack_info

_RULES_PATH=Path(__file__).parent/'bilibili-content-rules.json'
if not _RULES_PATH.is_file():_RULES_PATH=Path(__file__).parent/'apps/shared/bilibili-content-rules.json'
_CONTENT_RULES=json.loads(_RULES_PATH.read_text(encoding='utf-8'))

def content_decision(title,author,description='',tags=None):
    rules=_CONTENT_RULES
    title=unicodedata.normalize('NFKC',title);description=unicodedata.normalize('NFKC',description)
    hit=lambda key,text:bool(re.search(rules[key],text,re.I))
    decision=lambda kind,reason,candidate=False:{'kind':kind,'reason':reason,'candidate':candidate}
    spec=all(re.search(pattern,description,re.I) for pattern in rules['structuredPack'])
    project=hit('minecraftProject',description)
    strong_mc_body=hit('minecraftPackContext',description) or project or (spec and hit('minecraftVersion',description)) or (hit('packObject',description) and hit('minecraftVersion',description) and hit('minecraftLoader',description))
    mc_identity=hit('minecraft',title+'\n'+description) or strong_mc_body or any(str(t).strip().lower() in rules['minecraftTags'] for t in tags or [])
    if hit('irrelevant',title):return decision('irrelevant','标题指向AI或软件整合包')
    if hit('otherGame',title) and not hit('minecraft',title) and (not project or hit('explicitOtherGame',title)):
        return decision('uncertain','标题含其他游戏名称，尚缺足够的MC整合包项目依据，不能只靠题材词或标签判断') if strong_mc_body or hit('minecraftVersion',title) else decision('irrelevant','标题指向其他游戏；MC标签或网盘链接不能证明是MC整合包')
    if hit('nonPack',title):return decision('non_pack','内容指向单模组、材质、光影、模型、地图或数据包')
    if hit('mapBundle',title) and not (mc_identity and hit('modBundle',description)):return decision('uncertain','标题涉及地图整合包，但现有简介不足以确认同时包含一组MC模组')
    if hit('modFeature',title):return decision('non_pack','主要介绍单模组或模组推荐，标题提到整合包用途不能当作整合包发布')
    if hit('featureRelease',title):return decision('non_pack','发布对象是统计表、补丁或武器包，不能当作整合包发布')
    if hit('roundup',title):return decision('roundup','推荐合集、排行榜或求包视频不能对应一款整合包')
    if hit('gameplay',title) or hit('gameplayAuthor',author):return decision('gameplay','标题或账号标注实况、录播、速通或分集内容')
    if hit('unreleased',title) and not hit('announcement',title):return decision('uncertain','标题说明尚未发布、开发计划或仅预览，不能把计划当作已发布整合包')
    if hit('firstReleaseFuture',description) and not hit('announcement',title):return decision('uncertain','简介仍说明首个版本将在未来发布，现有快照不能确认已发布')
    if hit('serverPromotion',title):return decision('promotion','主要内容为服务器招募、充值或福利推广')
    if hit('directPromotion',title) or sum(bool(re.search(pattern,title,re.I)) for pattern in rules['promotionMarkers'])>=2:return decision('promotion','标题出现直装、主播同款、购买或夸张解锁措辞，需核对实际发布者')
    if hit('paidPromotion',title+'\n'+description):return decision('promotion','资料要求私信或进群购买，另存供核对')
    pack_details=spec or project or hit('modBundle',description) or (hit('minecraftVersion',description) and hit('minecraftLoader',description))
    if hit('marketingClaim',title) and not pack_details:return decision('uncertain','标题有直装、白嫖或自取等获取宣传，但简介未提供足够的整合包构成或项目资料')
    private_promotion=any(not hit('privateNegation',match.group()) for match in re.finditer(rules['privatePromotion'],description,re.I))
    if private_promotion and not spec and not project:return decision('promotion','简介要求关注或私信获取，且缺少可核对的整合包规格或项目原页')
    if hit('shortLink',description) and not spec and not project and not strong_mc_body:return decision('uncertain','简介含跳转短链，未提供可核对的MC整合包资料；不访问短链推断内容')
    if hit('primaryTutorial',title):return decision('tutorial','视频主要讲模组攻略、整合包流程或操作指南，不是整合包发布或整体介绍')
    if hit('discussion',title):return decision('uncertain','主要讨论整合包相关话题，不能仅凭引用原页当作发布或整体介绍')
    if hit('tutorial',title) and not (hit('release',title) and (spec or project or strong_mc_body)):return decision('tutorial','视频主要讲下载、安装、制作或迁移操作')
    if hit('dynamicAcquisition',description) and not pack_details:return decision('uncertain','简介引导点头像去动态获取，未提供可核对的整合包构成或项目资料；标题不能单独证明实际发布内容')
    if not hit('packObject',title) and not spec and not project:return decision('non_pack','未明确发布或介绍整合包；单模组/枪包/模型汉化不能当整合包')
    if not mc_identity:return decision('uncertain','标题、简介和已观测标签不足以确认Minecraft整合包')
    original_claim=hit('originalClaim',title) and not hit('notOriginalClaim',title)
    if hit('secondary',title) and not original_claim:return decision('showcase','标题标注分享、推荐或转载；项目原页、下载链接和视频日期不能证明是UP主原创发布',True)
    if original_claim:return decision('release','标题明确声称自制或本人制作；保留发布线索，作者归属仍需原页核验',True)
    if hit('announcement',title):return decision('announcement','具名MC整合包预告，尚不能确认新版本已发布',True)
    if hit('release',title):return decision('release','MC身份、整合包对象和发布/更新意图均有文字依据',True)
    if (project or spec) and hit('projectReleaseIntent',title):return decision('release','标题有发布/更新意图，简介提供MC整合包项目原页或具名规格',True)
    if hit('showcase',title):return decision('showcase','MC身份、整合包对象和介绍/展示意图均有文字依据',True)
    if spec and hit('minecraftVersion',description):return decision('showcase','简介给出具名整合包、游戏版本和模组构成，仍需到原页核对',True)
    return decision('uncertain','现有资料不足以确认整合包发布或介绍；不新增入库')

def content_category(title,author,description='',tags=None):
    return content_decision(title,author,description,tags)['kind']

class InvalidPublicVideo(ValueError):pass
class UnavailablePublicVideo(InvalidPublicVideo):
    def __init__(self,message,true_code=-404):
        super().__init__(message);self.true_code=true_code
class RestrictedPublicVideo(InvalidPublicVideo):
    """A correctly identified single video is private/paid; do not stop the queue."""
    def __init__(self,message,reason_code):
        super().__init__(message);self.reason_code=reason_code

class _Parser(HTMLParser):
    def __init__(self):
        super().__init__();self.meta={};self.scripts=[];self.active=None;self.title=[];self.in_title=False
        self.error_texts=[];self.error_active=None;self.error_depth=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='title':self.in_title=True
        if tag=='meta' and a.get('content') is not None:
            name=a.get('property') or a.get('name');self.meta[name]=a['content']
        if tag=='script' and not a.get('src'):self.active=[]
        if tag=='div':
            if self.error_active is not None:self.error_depth+=1
            elif 'error-text' in a.get('class','').split():self.error_active=[];self.error_depth=1
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
        if tag=='script' and self.active is not None:
            self.scripts.append(''.join(self.active));self.active=None
        if tag=='div' and self.error_active is not None:
            self.error_depth-=1
            if not self.error_depth:self.error_texts.append(''.join(self.error_active).strip());self.error_active=None
    def handle_data(self,text):
        if self.in_title:self.title.append(text)
        if self.active is not None:self.active.append(text)
        elif self.error_active is not None:self.error_active.append(text)

def parse_public_video(html,bvid):
    if not re.fullmatch(r'BV[0-9A-Za-z]{10}',bvid):raise InvalidPublicVideo('Invalid BVID')
    parser=_Parser();parser.feed(html);state=None
    for script in parser.scripts:
        match=re.search(r'window\.__INITIAL_STATE__\s*=\s*',script)
        if match:
            try:state=json.JSONDecoder().raw_decode(script[match.end():])[0]
            except ValueError:raise InvalidPublicVideo('Initial state is not JSON')
            break
    if isinstance(state,dict):
        error=state.get('error');missing_video=state.get('videoData') or {}
        canonical=parser.meta.get('og:url')
        exact_url=canonical and canonical.rstrip('/')==f'https://www.bilibili.com/video/{bvid}'
        known_unavailable=isinstance(error,dict) and (
            error.get('trueCode')==-404 and (not canonical or exact_url)
            or error.get('trueCode')==62002 and error.get('message')=='稿件不可见' and exact_url
            or error.get('trueCode')==62012 and error.get('message')=='62012' and error.get('fromSpider') is False
               and exact_url and '当前稿件up主设置为仅自见' in parser.error_texts)
        # An official unavailable-video page is distinct from a source access
        # refusal. Require all observed signals, including the requested BVID.
        if (isinstance(error,dict) and type(error.get('code')) is int and error['code']==404
            and known_unavailable and state.get('bvid')==bvid
            and ''.join(parser.title).strip() in ('视频去哪了呢？_哔哩哔哩_bilibili','视频去哪了呢?_哔哩哔哩_bilibili')
            and isinstance(missing_video,dict) and not any(missing_video.get(k) for k in ('bvid','title','pubdate'))):
            raise UnavailablePublicVideo('Official video unavailable (initial-state 404)',error['trueCode'])
    if not isinstance(state,dict):raise InvalidPublicVideo('Missing or error initial state')
    if state.get('error'):raise InvalidPublicVideo('Unclassified initial-state error')
    video=state.get('videoData')
    if not isinstance(video,dict) or state.get('bvid')!=bvid or video.get('bvid')!=bvid:raise InvalidPublicVideo('BVID mismatch')
    if type(video.get('state')) is not int:raise InvalidPublicVideo('Missing or invalid publication state')
    if video['state']!=0:raise RestrictedPublicVideo('Video is not public','non-public-state')
    restriction_fields=['is_upower_exclusive','is_upower_play','is_upower_preview','is_chargeable_season']
    if any(k in video and type(video[k]) is not bool for k in restriction_fields):raise InvalidPublicVideo('Invalid restriction flag')
    if any(video.get(k) is True for k in restriction_fields):raise RestrictedPublicVideo('Paid or restricted video','paid-or-restricted')
    canonical=parser.meta.get('og:url')
    if canonical and canonical.rstrip('/')!=f'https://www.bilibili.com/video/{bvid}':raise InvalidPublicVideo('Canonical URL mismatch')
    if not isinstance(video.get('title'),str) or not isinstance(video.get('owner'),dict) or not isinstance(video['owner'].get('name'),str):raise InvalidPublicVideo('Missing identity fields')
    if type(video.get('pubdate')) is not int or video['pubdate']<=0:raise InvalidPublicVideo('Missing publication date')
    if 'video:release_date' in parser.meta:
        if int(datetime.fromisoformat(parser.meta['video:release_date'].replace('Z','+00:00')).timestamp())!=video['pubdate']:raise InvalidPublicVideo('Publication date mismatch')
    tags=[t['tag_name'] for t in state.get('tags',[]) if isinstance(t,dict) and isinstance(t.get('tag_name'),str)]
    return video,tags

def classify_video(video,tags):
    seconds=video.get('duration',0)
    seconds=seconds if type(seconds)is int and seconds>=0 else 0
    duration=f'{seconds//3600}:{seconds%3600//60:02d}:{seconds%60:02d}' if seconds>=3600 else f'{seconds//60}:{seconds%60:02d}'
    desc=video.get('desc') if isinstance(video.get('desc'),str) else ''
    info=extract_modpack_info(video['title'],desc,'','',author=video['owner']['name'],duration=duration,source_tags=tags)
    policy=content_decision(video['title'],video['owner']['name'],desc,tags)
    legacy_gameplay=info.get('is_let_play')
    if legacy_gameplay and policy['candidate']:
        # Crediting another pack author/original video is not gameplay evidence.
        # The shared policy already requires MC pack identity and release/showcase
        # evidence; a missing project URL cannot turn an author credit into gameplay.
        # Preserve the legacy title/author/duration refusals independently.
        title_evidence=extract_modpack_info(video['title'],'','','',author=video['owner']['name'],duration=duration,source_tags=tags)
        legacy_gameplay=title_evidence.get('is_let_play')
    accepted=info['is_genuine'];basis='existing filter with official MC identity tags'
    # Keep independent legacy quality refusals. The shared policy owns semantic
    # decisions: an incidental tutorial or a private acquisition method cannot
    # veto an otherwise evidenced publication, and cannot bypass a negative gate.
    semantic_reasons={'私信引流','纯教程','启动器教程','教学指南','无MC标识且无版本号','纯介绍无下载'}
    if not accepted and policy['candidate'] and not legacy_gameplay and (not info.get('is_spam_bait') or info.get('spam_reason') in semantic_reasons):
        accepted=True;basis='shared content policy confirms MC pack identity and publication/introduction evidence; legacy semantic flags retained as advisories'
    if legacy_gameplay:
        accepted=False;basis='legacy gameplay evidence; not a pack publication'
    category=policy['kind']
    # No metadata, private-acquisition exception or legacy flag can bypass the content gate.
    if not policy['candidate']:
        accepted=False;basis='content policy: '+category+'; '+policy['reason']
    acquisition_advisory=info.get('spam_reason')=='私信引流' or bool(re.search(r'私信|(?:关注|三连).*?(?:自动发送|自动私信|发送整合包)',desc))
    return {'accepted':accepted,'basis':basis,'contentCategory':category,'contentReason':policy['reason'],'contentPolicySchema':_CONTENT_RULES['schema'],'legacyFlags':{k:info.get(k) for k in ['is_genuine','is_let_play','is_spam_bait','spam_reason']},'privateAcquisitionAdvisory':acquisition_advisory,'duration':duration,'extracted':info}

def make_public_record(video,tags,html,observed_at):
    decision=classify_video(video,tags)
    if not decision['accepted']:return None,decision
    extracted=decision['extracted'];bvid=video['bvid']
    source=f'https://www.bilibili.com/video/{bvid}/'
    record={'platform':'bilibili','bvid':bvid,'url':source,'title':video['title'],'author':video['owner']['name'],'pub_timestamp':video['pubdate'],'pub_time':datetime.fromtimestamp(video['pubdate'],timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M'),'duration':decision['duration'],'source_tags':tags,'source_kind':'official-public-video-html','source_url':source,'source_observed_at':observed_at,'source_html_sha256':hashlib.sha256(html.encode()).hexdigest(),'pinned_comment_observed':False,'subtitle_observed':False,'download_links_observed':False,'source_field_provenance':{'title':'videoData.title','author':'videoData.owner.name','pub_timestamp':'videoData.pubdate','source_tags':'INITIAL_STATE.tags[].tag_name'},'classification_basis':decision['basis']}
    if isinstance(video.get('desc'),str):
        # Keep only a bounded excerpt. Do not replace a prior full description
        # with this excerpt or set the old full-desc-observed flag.
        record['description_excerpt']=video['desc'][:160]
        record['description_excerpt_truncated']=len(video['desc'])>160
        record['description_excerpt_observed']=True
        record['desc_observed']=False
        record['source_field_provenance']['description_excerpt']='videoData.desc[:160]'
        record['description_source_sha256']=hashlib.sha256(video['desc'].encode()).hexdigest()
    for k in ['mc_version','all_versions','loaders','categories','download_links','extract_code','qq_group','mod_count','has_server','pack_version','has_group_version','group_version_note']:
        if k in extracted:record[k]=extracted[k]
    # Preserve whole title version tokens: the legacy regex can reduce 2.0.0
    # to 0.0. Minecraft version tokens remain separately classified.
    title_versions=re.findall(r'(?<![\d.])(\d+\.\d+(?:\.\d+){0,2})(?![\d.])',video['title'])
    pack_tokens=list(dict.fromkeys(v for v in title_versions if v not in record.get('all_versions',[])))
    if len(pack_tokens)==1:
        record['pack_version']=pack_tokens[0]
        record['source_field_provenance']['pack_version']='whole version token in videoData.title; excludes extracted Minecraft versions'
    elif record.get('pack_version') and record['pack_version'] not in title_versions:
        record['pack_version']=''
    # Missing statements do not prove lack of a server or a group-only version.
    for k in ['has_server','has_group_version']:
        if not record.get(k):record[k]=None
    # Preserve query parameters in description links without requesting targets.
    public_urls=re.findall(r'https?://[^\s<>"\'，。；）】]+',video.get('desc') or '')
    for link in record.get('download_links',[]):
        matches=[u.rstrip('.,;)]') for u in public_urls if u.startswith(link.get('url','')) and link.get('url')]
        if len(matches)==1:link['url']=matches[0]
    record['description_download_links_observed']=isinstance(video.get('desc'),str)
    if decision['privateAcquisitionAdvisory']:record['acquisition_note']='公开介绍称需关注/私信获取；本次仅收录公开元数据，未获取私人链接。'
    for k in ['aid','cid','pic']:
        if k in video:record[k]=video[k]
    for target,sourcekey in [('views','view'),('likes','like'),('coins','coin'),('favorites','favorite'),('share','share'),('reply','reply'),('danmaku','danmaku')]:
        value=video.get('stat',{}).get(sourcekey)
        if type(value)is int and value>=0:record[target]=value
    return record,decision
