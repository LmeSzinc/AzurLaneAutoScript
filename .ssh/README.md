# GitHub SSH 配置说明

当前项目已生成专用的 GitHub 部署/交互 SSH 密钥对，存放在当前目录下：
- **私钥（绝对不能泄露）**：`id_ed25519`
- **公钥（需要复制到 GitHub）**：`id_ed25519.pub`

---

## 步骤 1：复制公钥内容

你可以直接打开 `id_ed25519.pub` 文件复制，或者复制下方文本：

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

### 2. 关联并推送到你的 Fork 仓库：
如果你在 GitHub 上 Fork 了仓库，使用 SSH 地址关联并推送：
```bash
# 添加或修改 origin 为 SSH 地址 (替换为你自己的 GitHub 路径)
git remote add origin git@github.com:你的GitHub用户名/AzurLaneAutoScript.git

# 推送当前特性分支
git push -u origin feat/api-mcp
```
