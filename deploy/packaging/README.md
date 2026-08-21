# Desktop 打包与分发

> 状态：已实现并在打包机验证（v0.1.1/v0.1.2）；构建与发布由
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

## 3. 发布（CI）

`.github/workflows/release.yml`：推 `v*` tag（或手动 dispatch）→ Windows runner
上 uv sync → 前端 `pnpm build` → PyInstaller sidecar（`version.txt = $GITHUB_REF_NAME`）
→ NSIS → 创建 GitHub Release 上传 `Alas_<ref>_x64-setup.exe`。

## 4. 已知权衡

- **卸载行为（实测）**：卸载器只删除壳 exe 与注册表项，侧车目录（~200MB）与
  用户数据保留，需手动清理残留目录。更新路径不受影响。
- 更新下载走 GitHub 资产地址（国内网络环境可能需要 VPN）。
