# GitHub SSH 配置说明

当前项目已生成专用的 GitHub 部署/交互 SSH 密钥对，存放在 `.ssh/` 目录下：
- **私钥（严禁提交与泄露）**：`.ssh/id_ed25519`
- **公钥（需要复制到 GitHub）**：`.ssh/id_ed25519.pub`

---

## 步骤 1：复制公钥内容

你可以直接打开 `.ssh/id_ed25519.pub` 文件复制，或者复制下方这一行内容：

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIM/kK9AGbio5SMIz45fQ21flemfy7pGiqrw9SkbRt2QQ alas_api_mcp
```

---

## 步骤 2：添加到 GitHub

1. 登录你的 GitHub 账号，打开 [GitHub SSH Keys 设置页面](https://github.com/settings/keys)。
2. 点击右上角绿色按钮 **"New SSH key"**。
3. 填写信息：
   - **Title**：可填写识别名称，如 `ALAS_API_MCP`
   - **Key type**：选择 `Authentication Key`
   - **Key**：将上面的公钥完整粘贴进输入框。
4. 点击 **"Add SSH key"** 保存。

---

## 步骤 3：验证与使用

当前仓库已经通过 Git 本地配置绑定了该私钥：
```bash
git config core.sshCommand "ssh -i .ssh/id_ed25519 -o IdentitiesOnly=yes"
```

### 1. 测试连接：
在项目根目录运行命令：
```bash
ssh -T -i .ssh/id_ed25519 git@github.com
```
若提示 `Hi <你的用户名>! You've successfully authenticated...` 即代表连接成功！

### 2. 推送到你的 Fork 仓库：
当前仓库已配置好 `origin` 指向 `git@github.com:ZerowindSE/AzurLaneAutoScript.git`：
```bash
# 推送当前特性分支到你的 Fork 仓库
git push -u origin feat/api-mcp
```

> **安全机制**：本项目已在 Git 远程配置和 Hook 中严密锁死了对官方上游（LmeSzinc）的推送权限，**禁止任何私自向 upstream 的 push 操作**，仅允许从 upstream pull/fetch 合并更新。
