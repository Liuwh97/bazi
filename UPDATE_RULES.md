# 更新规则

- 远程约定：`upstream` 指向上游 china-testing 仓库，`origin` 指向个人 fork（Liuwh97/bazi），主分支为 `master`。
- 同步上游最新代码：
  ```bash
  git checkout master
  git pull upstream master
  ```
  若有冲突，按提示解决后再提交。
- 提交本地修改并推送到个人 fork：
  ```bash
  git add .
  git commit -m "描述本次改动"
  git push origin master
  ```
- 同步上游后保持个人仓库最新：
  ```bash
  git pull upstream master
  git push origin master
  ```
- 不直接向上游推送，如需贡献上游请通过 fork 后提 PR。
