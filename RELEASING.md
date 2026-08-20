# 发布流程

PyPI 发布由 [`.github/workflows/publish.yml`](.github/workflows/publish.yml) 自动完成。正常发布只由 GitHub Release 触发，不响应普通分支推送、Pull Request 或单独推送标签；手动入口仅用于恢复已经失败的 Release 发布。

## Trusted Publisher 配置

PyPI 项目中的 GitHub Trusted Publisher 应与下列信息完全一致：

- Owner：`YANG-Zijie`
- Repository：`mdstyledocx`
- Workflow：`publish.yml`
- Environment：`pypi`

GitHub 仓库中应创建名为 `pypi` 的 Environment，并建议设置必要的审批人。发布不需要保存 PyPI API Token；发布作业通过 GitHub OIDC 获取短期凭证。

## 启用推送前检查

首次克隆仓库后运行：

```bash
git config core.hooksPath .githooks
```

此后每次 `git push` 前都会自动验证工作流 YAML 和全部远程 Action 引用，并运行测试与发布包构建。远程引用检查需要能够访问 GitHub。也可以随时手动运行：

```bash
./.githooks/pre-push
```

## 发布一个版本

1. 同步更新 `pyproject.toml` 中的 `project.version` 和 `src/mdstyledocx/__init__.py` 中的 `__version__`。
2. 将 `CHANGELOG.md` 和 `CHANGELOG.zh-CN.md` 中对应版本的 `Unreleased` / `尚未发布` 改为发布日期。
3. 运行测试和构建检查：

   ```bash
   uv sync --locked
   uv run python -m unittest discover -s tests -v
   uv build
   ```

4. 提交并推送版本修改，等待 CI 通过。
5. 在 GitHub 创建并发布 Release，标签必须为 `vX.Y.Z`，例如 `v0.2.0`。

发布工作流会再次运行测试，确认 Release 标签、`pyproject.toml` 和 `mdstyledocx.__version__` 三者版本一致，构建 wheel 与源码包，然后通过 Trusted Publishing 上传同一份构建产物到 PyPI。任一检查失败都会停止发布。

如果 Release 已经发布、但工作流在上传 PyPI 前失败，应先在默认分支修复工作流，再针对原标签手动重试，无需删除或重新创建 Release：

```bash
gh workflow run publish.yml --ref main -f tag=vX.Y.Z
```

执行恢复命令前，应先确认该版本尚未存在于 PyPI。
