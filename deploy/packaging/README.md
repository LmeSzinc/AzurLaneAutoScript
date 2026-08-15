# Desktop 打包与分发（阶段 D-3）

> 状态：方案落地 + 骨架配置完成；**PyInstaller 构建与 NSIS 打包需在目标 Windows 机器上执行并实测**（本仓库开发沙箱无法运行 PyInstaller/tauri build）。

## 目标架构

```
[Tauri 壳 (NSIS 安装包)]
  ├─ alas-shell.exe
  ├─ alas-backend-x86_64-pc-windows-msvc/   ← PyInstaller onedir sidecar（externalBin）
  └─ webapp dist（由 FastAPI 托管，壳启动后 navigate 到 http://127.0.0.1:22267）
```

- 壳进程启动 sidecar 后端（`resolve_python` 按 `alas-backend*.exe` 名字在可执行文件旁查找），等 stderr 出现 `Application startup complete` 后显示窗口并导航。
- 用户数据（config/、assets/、bin/）不能放在 Program Files 只读资源目录：**首次运行引导**把随包资源复制到用户数据目录（待实现，见下文"遗留事项"）。
- 更新：Tauri updater 插件（已注册 `updater:default` 权限 + `createUpdaterArtifacts: v1Compatible`）负责壳更新；后端 git+pip 更新器保留为**开发者通道**（`/update/*` API 不变）。

## 1. PyInstaller onedir sidecar（后端）

```powershell
uv tool install pyinstaller   # 或 pip install pyinstaller==6.19
pyinstaller --clean --noconfirm deploy/packaging/alas_backend.spec
```

产物在 `dist/alas-backend/`。随后复制到 Tauri 的 externalBin 目录并重命名主程序：

```powershell
$triple = "x86_64-pc-windows-msvc"
New-Item -ItemType Directory -Force webapp-tauri/src-tauri/binaries | Out-Null
Copy-Item -Recurse dist/alas-backend webapp-tauri/src-tauri/binaries/alas-backend-$triple/
# externalBin 主程序名 = 目录名 + .exe
Rename-Item webapp-tauri/src-tauri/binaries/alas-backend-$triple/alas-backend.exe `
            webapp-tauri/src-tauri/binaries/alas-backend-$triple/alas-backend-$triple.exe
```

**已打包机验证前不要合并 spec 改动**：`alas_backend.spec` 是草稿（数据目录清单按实际情况增删），构建后必须实测 OCR 冒烟 + 起服。

打包机前提（spec 内已注释）：
- 后端运行时工作目录需可写，且包含 `config/`、`assets/`、`bin/`、`log/`。
- 打包部署配置建议 `EnableReload: false`（更新由壳/Tauri updater 负责；`gui.py` 已加 `freeze_support()` 兜底）。

## 2. Tauri 壳构建与签名

```powershell
cd webapp-tauri
pnpm install          # 已提交 pnpm-lock.yaml，可复现安装
pnpm tauri build      # beforeBuildCommand=pnpm build 会自动重建 dist
```

### 更新签名（tauri-plugin-updater）
发布更新前设置环境变量（构建期嵌入公钥）：
```powershell
$env:TAURI_SIGNING_PRIVATE_KEY = "..."        # tauri signer generate 生成
$env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD = ""  # 可选
```
发布：把产物（`.msi/.exe` + `latest.json`）上传到更新端点，并在 `tauri.conf.json` 的
`plugins.updater.endpoints` 填入 `latest.json` 地址（当前为空数组，未发布更新前保持为空）。

### Windows 代码签名（Authenticode）
在签名机配置 `tauri.conf.json` 的 `bundle.windows.certificateThumbprint`（或按 Tauri 文档
用 signtool 环境变量），签名机需安装匹配的证书。当前未配置（无证书，不能填占位值）。

### WebView2
`bundle.windows.webviewInstallMode: downloadBootstrapper` 已配置：目标机缺 WebView2
Evergreen 时安装器自动下载引导程序（需要网络）。离线部署场景需另行内置 WebView2 安装包。

## 3. 遗留事项（阶段 D 未闭合，需真机迭代）

1. **首次运行数据目录引导**：把只读资源中的 config/assets/bin 复制到用户数据目录
   （`%APPDATA%\Alas` 之类），并把后端 cwd 指过去。当前壳把资源目录当 cwd，打包后
   不可写，必须先解决再发布。
2. **前端 updater UI**：SPA 尚未接 `@tauri-apps/plugin-updater`（npm 包）做
   check/download/install；发布通道确定后再接。
3. spec 草稿需在打包机跑通并固化为 CI 步骤（阶段 E/F）。
4. NSIS 安装包需实测：安装/卸载/托盘/单实例/开机行为。
