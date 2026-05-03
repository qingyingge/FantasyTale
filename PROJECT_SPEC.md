# 项目特殊规范

## 发布流程

每次发布版本时执行以下步骤：

1. **更新 README.md** - 在 "游戏版本" 部分添加新版本信息（标记为当前版本）
2. **提交代码** - `git add` + `git commit`
3. **推送到远程** - `git push`
4. **创建 Git Tag** - `git tag -a v{x.y.z} -m "发布说明"`
5. **推送 Tag** - `git push origin v{x.y.z}`
6. **创建压缩包** - 放在项目根目录，**直接压缩源文件**，不要先复制到其他目录再压缩
7. **GitHub Release** - 使用 gh 命令或手动创建，包含标题和发布内容

### 压缩包制作命令
```powershell
# 在项目根目录执行，直接压缩源文件（排除 pycache 和 saves）
Compress-Archive -Path game.py, launcher.py, build.py, run.bat, requirements.txt, README.md, LICENSE, .gitignore, src, data -DestinationPath "FantasyTale_v{x.y.z}.zip"
```

## CHANGELOG 维护

项目根目录下的 `CHANGELOG.md` 用于记录每次提交的内容。

### 流程
1. 每次提交时在 CHANGELOG.md 中记录本次提交内容（追加到文件）
2. 用户要求发布版本时，清空 CHANGELOG.md 内容（保留文件，仅清空修改记录）
3. CHANGELOG.md 应加入 .gitignore

## 文件清理规范

- 删除不再使用的文件（如 src/models.py）
- 发布前检查是否有临时文件需要清理
- 确保 __pycache__ 目录不进入版本控制

## 其他规范

- 禁止提交压缩包到 Git（已在 .gitignore 中配置）
- 发布后更新 CHANGELOG.md 记录