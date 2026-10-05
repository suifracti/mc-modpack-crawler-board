import re
from typing import Any, Dict, List

def extract_modpack_info(title: str, desc: str, pinned_comment: str, subtitle_text: str='', author: str='', duration: str='', source_tags=None) -> Dict[str, Any]:
    full_text = f'{title}\n{desc}\n{pinned_comment}\n{subtitle_text}'
    mc_tag_names = {'我的世界', '我的世界整合包', 'minecraft', 'mc', 'mc整合包', 'minecraft整合包'}
    has_mc_source_tag = any((isinstance(tag, str) and tag.strip().casefold() in mc_tag_names for tag in source_tags or []))
    mc_context_text = full_text + ('\nMinecraft' if has_mc_source_tag else '')
    dur_sec = 0
    if duration:
        parts = duration.split(':')
        try:
            if len(parts) == 2:
                dur_sec = int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                dur_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except Exception:
            pass
    has_pack_title = bool(re.search('(?:整合包|模组包|懒人包|整合客户端)', title))
    has_action_title = bool(re.search('(?:更新|发布|首发|公测|上线|推出|自制|原创|开源|汉化版?|重[制置]版?|正式版|测试版|抢先版|先行版|体验版|出炉|完工|制作完成|分享|下载|v?\\d+\\.\\d+(?:\\.\\d+)?)', title, re.I))
    is_series = bool(re.search('(?:第\\s*[0-9一二三四五六七八九十百]+\\s*[集期话季篇回]|(?<![0-9a-zA-Z])(?:[Pp]|Part|EP)\\.?\\s*[0-9]{1,3}(?![0-9a-zA-Z]|fps|帧)|更新至\\s*[Pp]\\s*\\d+|[（\\(]更新至\\s*[Pp]?\\s*\\d+\\s*[集期])', title, re.I))
    is_let_play_commentary = bool(re.search('(?:【[^】]*(?:实况|解说|录播)[^】]*】|实况|生存实况|生存记|生存日记|一口气(?:看完|通关|肝完|爽玩)?|(?:实况|通关|剧情|全流程|流程|深度|速通|纯享)?解说|通关全程|全程实况|通关实况|通关记录|全流程通关|实况全程|纯享版|完结撒花|[【\\[\\(](?:实况|纯享|解说|录播|切片|游戏实况|通关实况|全程实况|开箱|整活)[】\\]\\)]|录播|切片|直播回放|录像回放|直播录像|录播回放|主播被迫断更|开局(?:就)?[坐牢受难暴毙无敌神装起飞破防痛苦折磨]|二周目|一周目|生存档|游玩记录|纯游玩|游戏实况|游戏解说|学玩|试玩(?!\\s*版).*?(?:模组|整合包|生存)|整合包#\\d+)', title, re.IGNORECASE))
    is_let_play = is_series or is_let_play_commentary
    if author == '马福' and dur_sec > 3600:
        is_let_play = True
    elif author == '籽岷' and '试玩' in title and (not re.search('试玩版', title)):
        is_let_play = True
    elif author == 'GreatCoffee' and dur_sec > 3600:
        is_let_play = True
    is_single_pack_release = bool(re.search('(?:自制|原创)?\\s*(?:整合包|模组包)\\s*(?:发布|更新|公测|首发|上线|推出|正式版|v\\d+)', title, re.I))
    is_recommendation_roundup = False
    if not is_single_pack_release or re.search('(?:\\d+|几|[一二三四五六七八九十])款', title):
        is_recommendation_roundup = bool(re.search('(?:最全.*?(?:整合包|模组包)?推荐|必玩[^\\n，。！？!?,]{0,15}?(?:整合包|模组包)?推荐|游玩推荐|(?:整合包|模组包)推荐榜|(?:整合包|模组包)盘点|(?:整合包|模组包)合集|(?:整合包|模组包)合辑|(?:整合包|模组包)排行|(?:盘点|推荐|精选)(?:\\d+|几|[一二三四五六七八九十])款|有哪些.*?(?:整合包|模组包)|(?:整合包|模组包)漫谈|(?:神仙|宝藏|好玩(?:的)?)(?:MC|我的世界)?整合包推荐|^[【\\[\\(]?\\s*(?:(?:MC|我的世界)?整合包|模组包)推荐\\s*[】\\]\\)]?|^[【\\[\\(]?\\s*(?:\\d+月|[一二三四五六七八九十]+月|暑[假期]|年度|最新)?\\s*推荐[！!：:\\s])', title, re.IGNORECASE))
    is_texture_or_resource = False
    if re.search('(?:光影整合包|材质整合包|皮肤整合包|数据包整合|超强光追材质|全物品3D模型与材质|Action&Stuff|Actions&stuff|Actions?&(?:amp;)?stuff)', title, re.I):
        is_texture_or_resource = True
    elif re.search('^[【\\[\\(]?(?:材质包|光影包|资源包|皮肤包|数据包)(?:发布|分享|推荐|展示|下载)', title, re.I):
        is_texture_or_resource = True
    elif re.search('(?:纯数据包|数据包发布|数据包分享|材质分享|光影分享|纯材质|手感材质|PVP材质|光影推荐|材质推荐|纹理包|皮肤包)', title, re.I):
        if re.search('(?:整合包|模组包)', title) and re.search('(?:自带|内置|附带|包含|搭载|专属|搭配|配有|配带|含).*?(?:材质|光影|资源)', title):
            is_texture_or_resource = False
        else:
            is_texture_or_resource = True
    elif re.search('(?:材质包|光影包|资源包)$', title) and (not re.search('(?:整合包|模组包)', title)):
        is_texture_or_resource = True
    versions = re.findall('(?<![0-9.])1\\.(?:21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|2)(?:\\.\\d+)?(?![0-9.])', full_text)
    seen = set()
    clean_versions = [v for v in versions if not (v in seen or seen.add(v))]
    loaders = re.findall('(?i)(?<![a-zA-Z0-9])(neoforge|fabric|forge|quilt)(?![a-zA-Z0-9])', full_text)
    loaders_clean = list(set([l.capitalize() for l in loaders]))
    download_links = []
    pan_patterns = [('百度网盘', 'https?://pan\\.baidu\\.com/(?:s/[a-zA-Z0-9_\\-]+|share/init\\?surl=[a-zA-Z0-9_\\-]+)'), ('夸克网盘', 'https?://pan\\.quark\\.cn/s/[a-zA-Z0-9_\\-]+'), ('123云盘', 'https?://(?:www\\.)?(?:123pan|123684|123865|123912)\\.com/s/[a-zA-Z0-9_\\-]+'), ('蓝奏云', 'https?://[a-zA-Z0-9_\\-]+\\.(?:lanzou[a-z]?|lanzn|lanzo)\\.com/[a-zA-Z0-9_\\-]+'), ('阿里云盘', 'https?://www\\.(?:aliyundrive|alipan)\\.com/s/[a-zA-Z0-9_\\-]+'), ('迅雷云盘', 'https?://pan\\.xunlei\\.com/s/[a-zA-Z0-9_\\-]+'), ('腾讯微云', 'https?://share\\.weiyun\\.com/[a-zA-Z0-9_\\-]+'), ('GitHub', 'https?://github\\.com/[a-zA-Z0-9_\\-]+/[a-zA-Z0-9_\\-]+/(?:releases|archive)[^\\s，,。\\n]*'), ('CurseForge', 'https?://(?:www\\.)?curseforge\\.com/minecraft/modpacks/[a-zA-Z0-9_\\-]+'), ('Modrinth', 'https?://modrinth\\.com/modpack/[a-zA-Z0-9_\\-]+'), ('MC百科', 'https?://www\\.mcmod\\.cn/modpack/\\d+\\.html'), ('星原社区', 'https?://www\\.xyebbs\\.com/resources/\\d+'), ('QQ频道', 'https?://pd\\.qq\\.com/g/[a-zA-Z0-9_\\-]+'), ('B站直达短链', 'https?://b23\\.tv/[a-zA-Z0-9%\\-_?=&]+'), ('磁力链接', 'magnet:\\?xt=urn:btih:[a-zA-Z0-9]+'), ('外链下载', 'https?://[a-zA-Z0-9_\\-\\.]+\\.(?:top|cn|com|net|org|xyz)/[a-zA-Z0-9_\\-/\\.]+')]
    for pan_name, pat in pan_patterns:
        matches = re.findall(pat, full_text)
        for m in matches:
            if not any((x in m for x in ['bilibili.com', 'hdslb.com', 'rainyun.com'])):
                if m not in [x['url'] for x in download_links]:
                    download_links.append({'type': pan_name, 'url': m})
    pwd_match = re.search('(?:提取码|密码|访问码|解压码|提取|pwd|code)[:：\\s]*([a-zA-Z0-9]{4,8})', full_text, re.IGNORECASE)
    extract_code = pwd_match.group(1) if pwd_match else ''
    qq_match = re.search('(?<!\\d)(?:QQ群|交流群|内测群|粉丝群|玩家群|群号?|官方群)[:：\\s]*([0-9]{6,12})(?!\\d)', full_text)
    qq_group = qq_match.group(1) if qq_match else ''
    mod_count_match = re.search('(?:模组数量|mod数量|模组数|包含)[:：\\s]*(\\d+)', full_text, re.IGNORECASE)
    mod_count = mod_count_match.group(1) if mod_count_match else ''
    categories = []
    cat_keywords = [('科技', ['科技', '工业', '无中生有', '机械', '格雷', 'ae2', '应用能源', '热力']), ('魔法', ['魔法', '植物魔法', '神秘', '血魔法', '铁魔法', '巫术']), ('冒险', ['冒险', '地牢', '遗迹', 'rpg', '探索', '交错次元', '暮色']), ('宝可梦', ['宝可梦', '神奇宝贝', '方可梦', 'pixelmon', 'cobblemon']), ('空岛', ['空岛', '海岛', '石头世界', '单方块', '贫瘠']), ('末日/生存', ['末日', '丧尸', '行尸走肉', '生化', '灾变', '寄生虫', '极限生存', '硬核']), ('战斗/枪械', ['枪械', '射击', '塔科夫', '拔刀剑', '大太刀', '动作', '战斗爽']), ('魔改', ['魔改', '专家', '魔改科技', '合成魔改', '任务线', '魔改线']), ('休闲/建筑', ['休闲', '养老', '装饰', '建筑', '农业', '烹饪', '美食', '农夫乐事'])]
    text_lower = full_text.lower()
    for cat_name, kw_list in cat_keywords:
        if any((kw in text_lower for kw in kw_list)):
            categories.append(cat_name)
    if not download_links and (not qq_group):
        cred = re.search('(?:整合包)?(?:原?作者|制作人|制作者)\\s*[:：]\\s*@([^\\s，,。\\n]+)', desc)
        if cred:
            c_name = cred.group(1).strip()
            if author and c_name.lower() not in author.lower() and (author.lower() not in c_name.lower()):
                is_let_play = True
        if re.search('整合包(?:宣传|发布|原|原版)?视频\\s*[:：]\\s*(?:https?://[^\\s]+|BV[a-zA-Z0-9]+)', desc, re.I):
            is_let_play = True
    is_spam_bait = False
    spam_reason = ''
    if re.search('(?:有没有.*?推荐我玩|求整合包推荐|求个整合包|有什么.*?整合包推荐我玩|推荐我玩啊|谁有.*?整合包|大家有没有.*?整合包|有没有什么整合包推荐)', title):
        is_spam_bait = True
        spam_reason = '求整合包推荐'
    elif re.search('(?:模组码|已加入整合包|迁移管理器|女仆档案|单模组|单个模组)', title):
        is_spam_bait = True
        spam_reason = '单模组/工具'
    elif re.search('(?:道歉！说明！补偿|关于整合包发布.*?道歉|整合包发布.*?延期|整合包延期发布)', title):
        is_spam_bait = True
        spam_reason = '延期道歉说明'
    elif re.search('伪整合包', title):
        is_spam_bait = True
        spam_reason = '伪整合包'
    elif not download_links and (not qq_group) and re.search('(?:画饼|更新进度|可公开情报|开发日志|即将发布|发布前瞻|更新前瞻)', title):
        is_spam_bait = True
        spam_reason = '纯画饼/未发布/无包'
    elif not download_links and re.search('(?:私信(?:自动)?回复|自动私信|主动私信|私信发给你|打开和我的对话框|评论区(?:截图)?留言[，,、\\s]*(?:私信|私发|获取|领取|发你|发链接|自动回复)|回复["\\\'“”][^"\\\'“”]{1,10}["\\\'“”].*?私信|点个免费三连关注\\+一定要看完视频|请勿拖[拽动]进度条|三连\\+点个关注\\+私信|快点关注到\\d+可以自动发|关注卡卡er|链接不发.*?私信才会发|关注后私聊获取|真的有东西的|必须要三连|关注后看后台私信|私信才会发文件|首次发布整合包.*?不要白嫖|关注并回复.*?私聊|关注后回复["\\\'“”]?整合["\\\'“”]?)', full_text, re.I):
        is_spam_bait = True
        spam_reason = '私信引流'
    elif re.search('(?:(?:三端|双端|安卓\\+)?(?:PC\\+)?iOS(?:\\+手机|\\+安卓|\\+PC)?(?:三端)?直装|iOS直装|三端PC\\+iOS|全CG(?:动态)?|3000\\+娘化|3000多只娘化|动漫娘化|娘化内容|娘化宝可梦|全清凉mod|爆衣皮肤|无限内购|手机\\+PC双端(?:直装|分享)|手机/电脑都可玩\\s*全互通|保姆级安卓\\+联机教程~~附地址|天花板\\d+\\.\\d+版本|最强最好玩顶级\\d+\\.\\d+版本|无偿速存|火速存起来|免费白嫖啦|手慢真会错过|入坑血赚|玩嗨了！！！)', full_text, re.I):
        is_spam_bait = True
        spam_reason = '虚假双端/低俗吸睛'
    elif re.match('^bili_\\d{7,}$', author) or re.match('^[a-z]{10,}$', author) or re.match('^[a-zA-Z0-9][\\u4e00-\\u9fa5]{2,6}[a-zA-Z0-9]{4,}$', author) or re.match('^[\\u4e00-\\u9fa5]{2}\\d[A-Z]-[\\u4e00-\\u9fa5]{2}$', author) or (author in ['梦灵神奇宝贝', '我的世界神奇宝贝屁王', '我的世界旺仔', '我的世界神奇宝贝花火', '我的世界神奇宝贝阿宇', '我的世界神奇宝贝樱木', '山白嗄', '是山白呀', '世傲吖', '我的世界神奇宝贝君', '我的世界宝可梦呆呆', '姐姐比我小两岁', '口袋觉醒后台板', '我的世界方块宝可梦one']):
        is_spam_bait = True
        spam_reason = '机器账号/推销号'
    elif not download_links and (not qq_group) and (not desc.strip().replace('-', '').replace('无', '')):
        if re.search('(?:附地址|附带安装|双端直装|免费分享|全网最新|懒人整合包|解压即玩|火速存|无偿速存|自取)', title):
            if re.search('(?:【.*?】.*?分享[！!~]|双端|保姆级|最新分享|懒人版)', title):
                is_spam_bait = True
                spam_reason = '空壳骗流'
    elif re.search('(?:仅(?:演示|预览|展示)|未发布|暂未发布|未放出|暂不发布|不分享|暂无链接|纯演示|无下载(?!(?:限制|门槛|限速|速度限制)))', title):
        is_spam_bait = True
        spam_reason = '未发布/仅演示预览'
    elif 0 < dur_sec <= 15 and (not download_links) and (not qq_group) and re.search('(?:前瞻|预告|更新计划|战争地带发布)', title):
        is_spam_bait = True
        spam_reason = '超短空壳预告'
    elif re.search('(?:明末|渊虚之羽|守望先锋|斗阵特攻|overwatch|lspdfr|侏罗纪世界进化|动物园之星|(?:switch|ns版).*?(?:大气层|特斯拉|超频|金手指|破解)|天马(?:\\d+|前端|模拟器)|【致命解药】|致命解药.*?整合包)', title, re.I):
        is_spam_bait = True
        spam_reason = '非MC游戏/独立软件/硬件固件'
    elif re.search('(?:ai绘画|stable\\s*diffusion|sd\\s*webui|comfyui|msst.*?webui).*?(?:整合包|一键包)|(?:整合包|一键包).*?(?:ai绘画|stable\\s*diffusion|comfyui)', title, re.I):
        is_spam_bait = True
        spam_reason = 'AI工具整合包'
    elif re.search('(?:七日杀|艾尔登法环|老头环|荒野大镖客|赛博朋克|辐射4|上古卷轴|天际线|都市天际线|模拟人生|博德之门|生化危机|暗黑破坏神|文明6|群星|十字军之王|骑马与砍杀|黑神话|幻兽帕鲁|palworld|泰拉瑞亚|terraria|星露谷|stardew|饥荒|巫师3|只狼|gta5|gta6|侠盗猎车)', full_text, re.I):
        has_mc_context = bool(re.search('(?i)(?:我的世界|minecraft|方块|网易mc|forge|fabric|neoforge|quilt|rlcraft|gtnh|gregtech|pcl|hmcl|curseforge|modrinth|(?:^|[^a-zA-Z0-9])mc(?:[^a-zA-Z0-9]|$)|mc整合|mc模组|mc发布|mc版本|1\\.(?:21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|2))', mc_context_text))
        if not has_mc_context and (not download_links) and (not qq_group):
            is_spam_bait = True
            spam_reason = '非MC单机游戏'
    elif not download_links and (not qq_group) and (not bool(re.search('(?i)(?:我的世界|minecraft|方块|网易mc|forge|fabric|neoforge|quilt|rlcraft|gtnh|gregtech|pcl|hmcl|curseforge|modrinth|(?:^|[^a-zA-Z0-9])mc(?:[^a-zA-Z0-9]|$)|mc整合|mc模组|mc发布|mc版本)', mc_context_text))) and (not bool(re.search('(?<![0-9.])1\\.(?:21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|2)(?:\\.\\d+)?(?![0-9.])', full_text))):
        is_spam_bait = True
        spam_reason = '无MC标识且无版本号'
    elif re.search('(?:如何迁移存档|迁移存档|宁然一隅整合包更新教程|使用的详细教程)', title):
        is_spam_bait = True
        spam_reason = '纯教程'
    elif '桃子味哒狐狸精' in author or re.search('(?:千人同服|永不删档|整合包服务器|永久开服拒绝删档)', title):
        is_spam_bait = True
        spam_reason = '服务器广告群发'
    elif not re.search('(?:整合包|模组包)', title) and re.search('(?:枪包|枪械包|武器包|弹药包|配件包|附属枪包|TacZ\\s*(?:附属|扩展|枪包)|TAC\\s*(?:附属|扩展|枪包)|TAC-Z\\s*(?:附属|扩展)|Point\\s*Blank\\s*(?:附属|扩展)|自制枪包|原创枪包|重置枪包|多枪包整合|guns\\s*and\\s*targets枪包|三角洲枪包|冲锋陷阵枪包|源石武器包|冲锋陷阵扩展包)', title, re.I):
        is_spam_bait = True
        spam_reason = '单模组枪包/武器包'
    elif re.search('(?:枪包|枪械包|武器包)', title) and (not re.search('(?:整合包|模组包)', title)):
        is_spam_bait = True
        spam_reason = '单模组枪包/武器包'
    elif not re.search('(?:整合包|模组包)', title) and re.search('(?:YSM\\s*模型|YSM\\s*动作|YSM\\s*整合|YSM.*?安装教程|车万女仆.*?模型|女仆模型包|CPM模型|自定义NPC模型|模型整合包|动作整合包|姿势包|骨骼动画包)', title, re.I):
        is_spam_bait = True
        spam_reason = '模型包/动作包'
    elif re.search('(?:[【\\[\\(]?(?:服务器发布|服务器宣传|服务器招募|服务器招新|新服开荒|新服发布|开服宣传|开荒公测)[】\\]\\)]?)', title):
        is_spam_bait = True
        spam_reason = '服务器发布/宣传'
    elif re.search('(?:(?:全新|自制|大型|原创|公益|商业|高版本|生化|RPG|战争|空岛|生存|养老|纯净|模组|互通|进服)服务器|.*?服务器.*?(?:你确定不来看看吗|即将更新内容|进群|公测|招人|招募|招新|开服啦))', title, re.I) and (not re.search('(?:整合包|模组包)\\s*(?:发布|更新|下载|分享)', title)):
        is_spam_bait = True
        spam_reason = '服务器宣传'
    elif re.search('(?:(?:安装和)?开服(?:联机)?教程|服务器搭建教程|FRP开服联机|自己的电脑也能开服)', title) and (not re.search('(?:整合包|模组包)\\s*(?:发布|更新|首发|公测)', title) or re.search('开服教程！|开服联机教程！|开服教程$|联机教程！', title)):
        is_spam_bait = True
        spam_reason = '开服联机教程'
    elif re.search('服务器', title) and re.search('(?:进服|服务器ip|服务器群|服务器介绍|欢迎加入.*?服)', full_text) and (not re.search('(?:整合包|模组包)\\s*(?:发布|更新|首发)', title)):
        is_spam_bait = True
        spam_reason = '服务器宣传'
    elif re.search('^[【\\[\\(]?(?:MC)?(?:模组|mod|Mod|MOD)发布[】\\]\\)]?', title):
        is_spam_bait = True
        spam_reason = '单模组发布'
    elif re.search('(?:模组|mod|Mod)更新', title) and (not re.search('(?:整合包|模组包)(?:.*?)(?:更新|发布)', title)) and (not re.search('(?:更新|发布)(?:.*?)(?:整合包|模组包)', title)):
        is_spam_bait = True
        spam_reason = '单模组更新'
    elif re.search('(?:整合包制作$|整合包制作[，,、\\s]|制作自己的(?:宝可梦)?整合包|教你.*?制作.*?整合包|整合包制作教学|手把手教你做整合包|如何制作整合包)', title) and (not re.search('(?:正式)?发布|公测|首发|全新更新|v\\d+\\.\\d+更新', title) or re.search('(?:2分钟做自己的|傻瓜式教学|制作自己的.*?整合包)', desc) or re.search('2分钟下载[，,]\\s*整合包制作', title)):
        is_spam_bait = True
        spam_reason = '整合包制作教学'
    elif re.search('(?:整合包启动教程|启动器教程|启动教程|启动教学)', title, re.I):
        is_spam_bait = True
        spam_reason = '启动教程'
    elif not re.search('(?:整合包|模组包|魔改包|懒人包)\\s*(?:发布|更新|公测|首发|v\\d+)', title, re.I) and re.search('(?:[一二三四五]分钟教你|手把手教你|教你(?:如何|怎样|怎么|安装|下载|汉化|制作|开服|配置)|如何安装|怎么安装|如何下载|怎么下载|如何开服|怎么开服|还不会(?:安装|下载)|详细步骤|看了必会)', title, re.I):
        is_spam_bait = True
        spam_reason = '教学指南'
    elif re.search('(?:汉化补丁(?:发布|安装|分享)?|单独汉化|汉化教程|模组汉化教程|保姆级汉化教程)', title, re.I):
        is_spam_bait = True
        spam_reason = '汉化补丁'
    elif re.search('(?:启动器发布|pcl2?发布|hmcl发布|fcl发布|bakaxl发布|启动器更新|\\[软件发布\\]|【软件发布】|整合包生成器|模组包打包器|整合包一键移植器)', title, re.I):
        is_spam_bait = True
        spam_reason = '软件/工具发布'
    elif re.search('(?:材质包发布|光影包发布|皮肤包发布)', title, re.I):
        is_spam_bait = True
        spam_reason = '材质光影'
    elif re.search('^[【\\[\\(]?(?:FCL|PCL|HMCL|BakaXL|折叠启动器|启动器)教程', title, re.I) or re.search('(?:启动器教程|教会你用手机玩Java版.*?整合包下载安装及更新教程)', title):
        is_spam_bait = True
        spam_reason = '启动器教程'
    elif re.search('【汉化发布】', title) and (not re.search('(?:整合包|模组包)', title)):
        is_spam_bait = True
        spam_reason = '汉化补丁'
    elif author in ['丶畜生'] or re.search('(?:畜生|傻逼|脑瘫)', author):
        is_spam_bait = True
        spam_reason = '低俗违规UP主'
    elif re.search('(?:汉化资源包|汉化材质包|汉化光影包)', title):
        is_spam_bait = True
        spam_reason = '汉化资源包'
    elif re.search('(?:介绍\\[发布\\]|介绍\\[更新\\])', title) and (not download_links) and (not qq_group):
        is_spam_bait = True
        spam_reason = '纯介绍无下载'
    elif re.search('1[3-9]\\d{9}整合包', title) or (re.search('1[3-9]\\d{9}', title) and (not desc.strip())):
        is_spam_bait = True
        spam_reason = '手机号营销号'
    has_action_or_resource = has_action_title or bool(download_links) or bool(qq_group)
    if not has_pack_title or not has_action_or_resource or is_texture_or_resource or is_let_play or is_recommendation_roundup or is_spam_bait:
        is_genuine = False
    else:
        is_genuine = True
    has_server = bool(re.search('(?:服务端|服务器端|开服包|开服|双端|服务器整合包|服务器端下载)', full_text))
    for dl in download_links:
        if re.search('(?:server|服务端|开服)', dl.get('type', '') + ' ' + dl.get('url', ''), re.I):
            has_server = True
    pack_version = ''
    pv_m = re.search('(?:处于|版本|version|ver|v)?\\s*([0-9]+\\.[0-9]+(?:\\.[0-9]+)?(?:[a-zA-Z0-9_\\-\\.]+)?)\\s*(?:初步测试|测试版|正式版|版本|阶段)', full_text, re.I)
    if pv_m:
        pack_version = pv_m.group(1).strip()
    else:
        pv_m2 = re.search('(?i)\\bv?([0-9]+\\.[0-9]+(?:\\.[0-9]+)?)\\b', title)
        if pv_m2 and pv_m2.group(1) not in ['1.20', '1.12', '1.16', '1.18', '1.19', '1.21', '1.7', '1.8']:
            pack_version = pv_m2.group(1).strip()
    has_group_version = False
    group_version_note = ''
    gv_pattern = '(?:进群体验|群文件|群里还有|群内首发|群内测试|群里更新|Q群下载|加群体验|群里下载|群内流转|群里版本|群里最新|群里另一个版本|全面换新)'
    if re.search(gv_pattern, pinned_comment):
        has_group_version = True
        group_version_note = pinned_comment.strip()
    elif re.search(gv_pattern, desc):
        has_group_version = True
        for line in desc.splitlines():
            if re.search(gv_pattern, line):
                group_version_note = line.strip()
                break
    return {'is_genuine': is_genuine, 'is_let_play': is_let_play, 'is_spam_bait': is_spam_bait, 'spam_reason': spam_reason, 'mc_version': clean_versions[0] if clean_versions else '未知', 'all_versions': clean_versions, 'loaders': loaders_clean, 'download_links': download_links, 'extract_code': extract_code, 'qq_group': qq_group, 'mod_count': mod_count, 'categories': categories, 'has_server': has_server, 'pack_version': pack_version, 'has_group_version': has_group_version, 'group_version_note': group_version_note}
