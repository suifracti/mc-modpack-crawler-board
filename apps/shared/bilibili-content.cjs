// One explainable policy for browsing archived records and admitting future HTML candidates.
const rules = require('./bilibili-content-rules.json');
const patterns = Object.fromEntries(Object.entries(rules).filter(([,v]) => typeof v === 'string').map(([k,v]) => [k, new RegExp(v, 'i')]));
const promotion = rules.promotionMarkers.map(p => new RegExp(p, 'i'));
const structured = rules.structuredPack.map(p => new RegExp(p, 'i'));
function classifyBilibiliContent(row) {
  const raw = row.raw || row;
  const title = String(row.title || '').normalize('NFKC'), author = String(row.author || row.owner?.name || '');
  const description = String(raw.desc || raw.description || raw.description_excerpt || row.summary || '').normalize('NFKC');
  const tags = Array.isArray(raw.source_tags) ? raw.source_tags : [];
  const full = title + '\n' + description;
  const spec = structured.every(p => p.test(description));
  const project = patterns.minecraftProject.test(description);
  const strongMcBody = patterns.minecraftPackContext.test(description) || project || (spec && patterns.minecraftVersion.test(description)) || (patterns.packObject.test(description) && patterns.minecraftVersion.test(description) && patterns.minecraftLoader.test(description));
  const mcIdentity = patterns.minecraft.test(full) || strongMcBody || tags.some(t => rules.minecraftTags.includes(String(t).trim().toLowerCase()));
  const decision = (kind, label, reason, candidate = false) => ({ kind, label, reason, candidate });
  if (raw.content_policy_schema === rules.schema && raw.content_candidate === false) return decision(raw.content_category || 'uncertain', '入库核验未通过', String(raw.content_reason || raw.classification_basis || '最近公开HTML观察未通过内容核验，保留存档供核对'));
  if (patterns.irrelevant.test(title)) return decision('irrelevant', '非MC内容', '标题指向AI或软件整合包');
  if (patterns.otherGame.test(title) && !patterns.minecraft.test(title) && (!project || patterns.explicitOtherGame.test(title))) return strongMcBody || patterns.minecraftVersion.test(title) ? decision('uncertain', 'MC主题待核验', '标题含其他游戏名称，尚缺足够的MC整合包项目依据，不能只靠题材词或标签判断') : decision('irrelevant', '其他游戏', '标题指向其他游戏；MC标签或网盘链接不能证明是MC整合包');
  if (patterns.nonPack.test(title)) return decision('non_pack', '非整合包', '内容指向单模组、材质、光影、模型、地图或数据包');
  if (patterns.mapBundle.test(title) && !(mcIdentity && patterns.modBundle.test(description))) return decision('uncertain', '地图内容待核验', '标题涉及地图整合包，但现有简介不足以确认同时包含一组MC模组');
  if (patterns.modFeature.test(title)) return decision('non_pack', '模组内容', '主要介绍单模组或模组推荐，标题提到整合包用途不能当作整合包发布');
  if (patterns.featureRelease.test(title)) return decision('non_pack', '附属资料', '发布对象是统计表、补丁或武器包，不能当作整合包发布');
  if (patterns.roundup.test(title)) return decision('roundup', '合集 / 求包', '推荐合集、排行榜或求包视频不能对应一款整合包');
  if (patterns.gameplay.test(title) || patterns.gameplayAuthor.test(author)) return decision('gameplay', '实况 / 解说', '标题或账号标注实况、录播、速通或分集内容');
  if (patterns.unreleased.test(title)) return decision('uncertain', '发布状态待核验', '标题说明尚未发布、开发计划或仅预览，不能把计划当作已发布整合包');
  if (patterns.firstReleaseFuture.test(description)) return decision('uncertain', '首发状态待核验', '简介仍说明首个版本将在未来发布，现有快照不能确认已发布');
  if (patterns.serverPromotion.test(title)) return decision('promotion', '服务器推广', '主要内容为服务器招募、充值或福利推广');
  if (patterns.directPromotion.test(title) || promotion.filter(p => p.test(title)).length >= 2) return decision('promotion', '推广措辞', '标题出现直装、主播同款、购买或夸张解锁措辞，需核对实际发布者');
  if (patterns.paidPromotion.test(full)) return decision('promotion', '购买导流', '资料要求私信或进群购买，另存供核对');
  const packDetails = spec || project || patterns.modBundle.test(description) || (patterns.minecraftVersion.test(description) && patterns.minecraftLoader.test(description));
  if (patterns.marketingClaim.test(title) && !packDetails) return decision('uncertain', '获取宣传待核验', '标题有直装、白嫖或自取等获取宣传，但简介未提供足够的整合包构成或项目资料');
  const privatePromotion = (description.match(new RegExp(rules.privatePromotion, 'ig')) || []).some(t => !patterns.privateNegation.test(t));
  if (privatePromotion && !spec && !project) return decision('promotion', '私信导流', '简介要求关注或私信获取，且缺少可核对的整合包规格或项目原页');
  if (patterns.shortLink.test(description) && !spec && !project && !strongMcBody) return decision('uncertain', '导流待核验', '简介含跳转短链，未提供可核对的MC整合包资料；不访问短链推断内容');
  // A real named release may include secondary installation instructions.
  if (patterns.primaryTutorial.test(title)) return decision('tutorial', '攻略 / 教程', '视频主要讲模组攻略、整合包流程或操作指南，不是整合包发布或整体介绍');
  if (patterns.discussion.test(title)) return decision('uncertain', '杂谈待核验', '主要讨论整合包相关话题，不能仅凭引用原页当作发布或整体介绍');
  if (patterns.tutorial.test(title) && !(patterns.release.test(title) && (spec || project || strongMcBody))) return decision('tutorial', '操作教程', '视频主要讲下载、安装、制作或迁移操作');
  if (patterns.dynamicAcquisition.test(description) && !packDetails) return decision('uncertain', '获取信息待核验', '简介引导点头像去动态获取，未提供可核对的整合包构成或项目资料；标题不能单独证明实际发布内容');
  if (!patterns.packObject.test(title) && !spec) return decision('non_pack', '非整合包', '未明确发布或介绍整合包；单模组/枪包/模型汉化不能当整合包');
  if (!mcIdentity) return decision('uncertain', 'MC身份待核验', '标题、简介和已观测标签不足以确认Minecraft整合包');
  if (patterns.release.test(title)) return decision('release', '发布线索', 'MC身份、整合包对象和发布/更新意图均有文字依据', true);
  if ((project || spec) && patterns.projectReleaseIntent.test(title)) return decision('release', '发布线索', '标题有发布/更新意图，简介提供MC整合包项目原页或具名规格', true);
  if (patterns.showcase.test(title)) return decision('showcase', '介绍线索', 'MC身份、整合包对象和介绍/展示意图均有文字依据', true);
  if (spec && patterns.minecraftVersion.test(description)) return decision('showcase', '资料线索', '简介给出具名整合包、游戏版本和模组构成，仍需到原页核对', true);
  return decision('uncertain', '待核验', '现有资料不足以确认整合包发布或介绍；不新增入库');
}
module.exports = { classifyBilibiliContent };
