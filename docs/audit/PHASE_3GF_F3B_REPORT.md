# Phase 3G-F.3-B — Final Audit Integration Base

本报告只覆盖 B：Final Audit Integration Base。操作目录为
`D:/ai/work/mc-3gf-i3v2`；主工作目录、其他 worktree、全局 Git 配置均未写入。
本模块没有集成 runtime，没有执行最终 runtime integration、Truth Matrix 定稿或
production cutover。

## 1. 起点与提交验证

| 项目 | 结果 |
|---|---|
| starting HEAD | `d5ebebca8b30e894fcea876a77a2c5a54495d771` |
| branch | `integration/phase3gf-ab-v2` |
| worktree | `D:/ai/work/mc-3gf-i3v2` |
| `cbbfb58` | `commit`; 7 files, all under `pipeline/audit/**` or `tests/**` |
| `a690d3d` | `commit`; 1 file, `docs/audit/PHASE_3GF_F2B_REPORT.md` |
| forbidden runtime/cutover paths | none; no `apps/web/src/**`, grouping runtime, or cutover infra path |

执行过的只读核验包括：

```text
git cat-file -t cbbfb58
git cat-file -t a690d3d
git show --stat --name-status cbbfb58
git show --stat --name-status a690d3d
```

两份 tracked JSON 在 cherry-pick 前 `git diff` 为空，`git hash-object` 与
`git ls-files -s` 的 blob OID 完全一致；`git status --porcelain=v2` 的 dirty 标记
是 stale stat cache。只执行了目标文件的 `git update-index --refresh`，没有重生成、
丢弃或制造无意义 commit。

## 2. Cherry-pick 与范围隔离

严格按要求顺序执行：

| 顺序 | source | result | 冲突 |
|---:|---|---|---:|
| 1 | `cbbfb588262d06d386dab645deee88e0c4acb7c3` | `f97d7cb` | 0 |
| 2 | `a690d3dfddc66d4260960b83c9cece7bdb3af72a` | `d05ffea` | 0 |

未发生冲突，因此不存在 runtime 冲突解决。`git diff --name-only
d5ebebca8b30e894fcea876a77a2c5a54495d771..HEAD` 的变更只在 audit/docs/tests；
其中 `apps/web/src/**`、pipeline grouping runtime 与 cutover infra 的限定 diff
均为空。runtime untouched proof：

```text
git diff --name-only d5ebebc..HEAD -- apps/web/src        => empty
git diff --name-only d5ebebc..HEAD -- pipeline             => audit-only paths
git diff --name-only d5ebebc..HEAD -- pipeline/cutover*    => empty
```

## 3. Final evidence 层

已生成并提交：

- `build/audit/phase3gf_truth_matrix_reconciliation.json`
  - 明确是 `reconciliation_plan`，`final_status` 为 `PENDING`，没有写死 broad
    population under-merge 的最终状态。
  - `retire_or_rewrite` 包含 `old 涅槃-specific undermerge premise`。
  - `pending_runtime_result` 包含 `broad population undermerge status`。
  - `keep` 包含 `BILI-GRP-02 SUSPECT unless final evidence supports more`。
- `build/audit/phase3gf_integration_base_v3.json`
  - `infra_integrated=true`
  - `expanded_false_merge_audit_integrated=true`
  - `final_undermerge_adjudication_integrated=true`
  - `runtime_fix_integrated=false`
  - `runtime_accepted=false`
  - `truth_matrix_reconciliation_pending=true`
  - `production_cutover_performed=false`

Final adjudication evidence available：
`pipeline/audit/bilibili_undermerge_adjudication_v2.json` 与
`pipeline/audit/confirmed_undermerge_runtime_gate.json` 已在第二个提交中；
undermerge adjudication suite 26/26 通过，AMBIGUOUS 没有进入 gate。

涅槃 corrected evidence available：ledger 与
`docs/audit/PHASE_3GF_F2B_REPORT.md` 均可读取；本模块没有改写
`docs/FEATURE_TRUTH_MATRIX.md`，只把旧 premise 放入 reconciliation plan。

### gzip audit JSON 读取兼容

当前 worktree 没有既有 `.json.gz` audit artifact，因此没有重生成压缩标签或样本。
对现有 adjudication JSON 做了最小 I/O-only 兼容核验：原始 JSON 字节 hash 与 gzip
容器 hash 分开记录；解压后字节与原始 JSON 相同，JSON 语义对象相同。核验结果为：

```text
original_json_bytes_sha256       8987d38db353c77f13385da3b8f4a00a4e95eaaa90bd21de1075c49b5a2f1feb
gzip_container_bytes_sha256      4719cd7deed270c64e593e1320353d3532da7121964352e54be33f19534ac602
decompressed_json_bytes_sha256   8987d38db353c77f13385da3b8f4a00a4e95eaaa90bd21de1075c49b5a2f1feb
decompressed_bytes_equal_original True
decompressed_semantic_equal       True
labels_regenerated                False
sample_population_reduced         False
ground_truth_replaced              False
```

## 4. 测试记录

每条日志都写入运行时 SHA 与完整命令；测试时 SHA 均为
`d05ffeae0e2dcc68726b30fdae00bbd331b328b5`。日志目录：
`D:/ai/work/mc-3gf-i3v2/build/audit/test-logs`。

| 测试 | 完整命令 | 退出码 | 日志绝对路径 |
|---|---|---:|---|
| typecheck | `npm --prefix apps/web run typecheck` | 0 | `D:/ai/work/mc-3gf-i3v2/build/audit/test-logs/01-typecheck.log` |
| Vitest | `npm --prefix apps/web test` | 0 | `D:/ai/work/mc-3gf-i3v2/build/audit/test-logs/02-vitest.log` |
| manifest hardening | `python -m unittest tests.test_manifest_hardening -v` | 0 | `D:/ai/work/mc-3gf-i3v2/build/audit/test-logs/03-manifest-hardening.log` |
| cutover transaction | `python -m unittest tests.test_cutover_transaction -v` | 0 | `D:/ai/work/mc-3gf-i3v2/build/audit/test-logs/04-cutover-transaction.log` |
| population audit v2 | `python -m unittest tests.test_bilibili_population_audit_v2 -v` | 0 | `D:/ai/work/mc-3gf-i3v2/build/audit/test-logs/05-population-audit-v2.log` |
| undermerge adjudication | `python -m unittest tests.test_bilibili_undermerge_adjudication -v` | 0 | `D:/ai/work/mc-3gf-i3v2/build/audit/test-logs/06-undermerge-adjudication.log` |
| feature truth matrix, attempted unittest entry | `python -m unittest tests.test_feature_truth_matrix_contract -v` | 5; 0 tests discovered | `D:/ai/work/mc-3gf-i3v2/build/audit/test-logs/07-feature-truth-matrix.log` |
| feature truth matrix, file entry | `python tests/test_feature_truth_matrix_contract.py` | 0; 99 statuses, 60 samples, 6/6 platforms | `D:/ai/work/mc-3gf-i3v2/build/audit/test-logs/08-feature-truth-matrix-correct-entry.log` |
| gzip + production read-only check | `python -c gzip semantic compatibility + manifest/canonical/data read-only verification` | 0 | `D:/ai/work/mc-3gf-i3v2/build/audit/test-logs/09-gzip-and-production-readonly.log` |

第一个 Truth Matrix 命令失败原因是该文件使用函数式入口而非 unittest test
case；随后使用其正确入口成功，未隐瞒这次退出码 5。

## 5. Production state 与发布不变量

`build/production_state.json` 在本 worktree 缺失，因此
`production_build_commit` 是否仍指向已有 released commit：**unavailable**；
没有用旧报告或 integration HEAD 臆造该字段。

当前可验证证据：

- `build/manifests/frontend_modern_production.sha256.json` 校验为 2924/2924，
  missing=0、modified=0、extra=0，即 manifest 100%。manifest 的 source commit
  为已存在的 released commit `4bf5e0fe4c614f3e630ae242db2ed5b66ef95fea`，不是
  integration HEAD。
- 重新计算 `build/canonical.db` 的 SHA-256 为
  `b2ada3a65a0fbf77098841b17d04ef1cea4519a11c61b3862098229a15cfa919`，与既有
  发布审计基线一致。
- 重新计算 `converted_output/data` 为 2920 files、130570675 bytes，rollup
  `4c3a05ff06fd3051291543b050c6fa46d678b2a6f494012a97707e7eec534c9a`，与既有
  发布审计基线一致。
- 没有执行 cutover；没有写 `production_state.json`，没有修改 production
  payload。

## 6. Ref integrity、clean proof 与最终状态

最终验证命令：

```text
git show-ref --verify refs/heads/integration/phase3gf-ab-v2
git rev-parse refs/heads/integration/phase3gf-ab-v2
git cat-file -t refs/heads/integration/phase3gf-ab-v2
git rev-parse HEAD
git cat-file -t HEAD
```

这些值在最终提交后核对为同一个 commit object；没有隐藏、删除、手工改写 loose
ref 或 packed-refs，也没有做 hidden-ref 测试。

最终 `git status --porcelain=v2` 为空。测试期间出现的 tracked JSON stale stat
标记在最终 refresh 后 OID 仍与 index/HEAD 一致；没有真实内容修改。

最终状态：

- `production_state`: unavailable（state 文件缺失）
- `manifest`: verified 100%
- `canonical`: unchanged by recomputation
- `data rollup`: unchanged by recomputation
- `runtime`: untouched
- `Truth Matrix`: not finalized
- `production cutover`: not performed
- `final HEAD`: `dbaa5679fea4ce0a3a85c3342456338899e1ba86`
