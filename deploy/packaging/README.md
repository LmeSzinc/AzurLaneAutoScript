# Desktop 打包与分发

> 状态：已实现并实测（260821 起采用日期版本命名）；构建与发布由
> `.github/workflows/release.yml` 在 CI 完成。

## 目标架构

```
[NSIS 安装包]（currentUser，如 %LOCALAPPDATA%\Programs\Alas）
  ├─ alas-shell.exe           ← Tauri 壳
  └─ alas-backend/            ← PyInstaller onedir sidecar（bundle.resources）
       ├─ alas-backend.exe
       ├─ version.txt         ← release tag
       └─ _internal/          ← 运行时 + 打包 datas
```

- 安装目录 = 用户数据目录：`config/ log/ assets/ bin/` 与壳并列。首次运行由壳从
  `alas-backend/_internal/` 播种；NSIS 更新只覆盖安装清单里的文件（exe + sidecar），
  用户数据天然保留。
- 壳启动 `alas-backend.exe gui.py --port <port>`（cwd = 安装目录），HTTP 轮询端口
  就绪后显示窗口。关窗/托盘退出/壳崩溃时 Job Object 整树收割后端。
- 更新：后端 `module/webui/updater.py` 拉取 GitHub release 列表，安装 = 静默执行
  setup.exe `/S /R`（安装器重启应用）。无 tauri updater 插件、无签名依赖。

## 1. PyInstaller onedir sidecar（后端）

```powershell
uv tool install "pyinstaller>=6.19"
pyinstaller --clean --noconfirm deploy/packaging/alas_backend.spec
# 产物：dist/alas-backend/（CI 里再写 version.txt = tag）
```

- spec 要点：`console=True`（未捕获异常走 stderr 而非隐藏的模态框）；datas 为
  assets/bin/config/module 子目录 + `webapp-tauri/dist`（SPA 由后端托管）；
  `pathex` 用绝对路径（含 `.venv/Lib/site-packages`，规避 packaging 20.9 遮蔽）。
- 冻结适配最小集：`module/base/paths.py::get_resource_root()`（_MEIPASS）、
  `module/logger.py` 的 `not frozen` chdir 守卫、`gui.py` 的 `freeze_support()`。

## 2. Tauri 壳构建

```powershell
cd webapp-tauri
pnpm install --frozen-lockfile
pnpm tauri build          # 产物 src-tauri/target/release/bundle/nsis/*-setup.exe
```

- `bundle.resources` 携带 `dist/alas-backend` → 安装后与 exe 并列（externalBin
  会压平 onedir 目录，不可用）。
- `installMode: currentUser`：安装目录可写，用户数据落在安装目录。
- `webviewInstallMode: downloadBootstrapper`：目标机缺 WebView2 时自动下载引导。
- 无 Authenticode 签名（SmartScreen 会提示；后续可加）。

## 3. 发布新版本（操作手册）

**版本规则**：对外版本 = tag = `YYMMDD`（如 `260821`）；资产名
`Alas_<tag>_x64-setup.exe`、应用内"当前版本"（version.txt）均为 tag 值。
Tauri 内部 version 字段必须是合法 semver，用对应日期 `YY.M.DD`（如 `26.8.21`）。

**发布一个版本只需三步**：

```powershell
# ① 改版本号（3 个文件 → YY.M.DD，如 26.8.22）
#    webapp-tauri/src-tauri/tauri.conf.json 的 "version"
#    webapp-tauri/src-tauri/Cargo.toml       的 version
#    webapp-tauri/package.json               的 "version"

# ② 提交推送
git add -A
git commit -m "release 260822"
git push fork master

# ③ 打 tag 并推送 → CI 自动构建并发布（约 12 分钟）
git tag 260822
git push fork 260822
```

CI 完成后 GitHub Release `260822` 自动创建，资产 `Alas_260822_x64-setup.exe`。
已安装的应用在 主页→更新器 刷新后即可看到并安装该版本。

**注意事项**：
- tag 不可重用：同一版本要重发时，先删掉再重打——
  `gh release delete 260822 --cleanup-tag && git tag -d 260822 && git tag 260822 && git push fork 260822`
- 推 tag 前先确认 ci.yml 通过（前端 lint/测试、pyright、导入冒烟）；
  推送 tag 前请确保所有改动已 commit 在 master 上——CI 构建的是 tag 指向的提交。
- 手动重跑（不发新版本）：Actions → Release → Run workflow（此时资产名会带
  分支名，仅用于调试，不建议）。
- 下载 GitHub 资产需代理（国内网络环境）。

## 4. 发布流水线内部（CI）

`.github/workflows/release.yml`：推 tag（名称不限，惯例 YYMMDD）→ Windows
runner 上 uv sync → 前端 `pnpm build` → PyInstaller sidecar（`version.txt =
$GITHUB_REF_NAME`）→ NSIS（`pnpm tauri build`）→ softprops/action-gh-release
创建同名 Release 并上传 `Alas_<ref>_x64-setup.exe`。

## 5. 已知权衡

- **卸载行为（实测）**：卸载器只删除壳 exe 与注册表项，侧车目录（~200MB）与
  用户数据保留，需手动清理残留目录。更新路径不受影响。
- 更新下载走 GitHub 资产地址（国内网络环境可能需要 VPN）。
