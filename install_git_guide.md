# Git安装指南

## 方法1：手动下载安装（推荐）

### 步骤1：下载Git
1. 访问官方下载页面：https://git-scm.com/download/win
2. 点击下载按钮，会自动下载最新版本的Git for Windows
3. 或者直接访问：https://github.com/git-for-windows/git/releases/latest

### 步骤2：安装Git
1. 运行下载的安装程序（通常是 `Git-2.51.0-64-bit.exe`）
2. 按照安装向导进行安装
3. 建议保持默认设置，特别是：
   - 选择 "Use Git from the command line and also from 3rd-party software"
   - 选择 "Use the OpenSSL library"
   - 选择 "Checkout Windows-style, commit Unix-style line endings"

### 步骤3：验证安装
安装完成后，重新打开PowerShell或命令提示符，运行：
```bash
git --version
```

## 方法2：使用Chocolatey（如果已安装）

如果您已经安装了Chocolatey包管理器：
```powershell
choco install git
```

## 方法3：使用Scoop（如果已安装）

如果您已经安装了Scoop包管理器：
```powershell
scoop install git
```

## 方法4：重新尝试Winget

如果网络条件允许，可以重新尝试：
```powershell
winget install Git.Git
```

## 安装后配置

### 设置用户信息
```bash
git config --global user.name "您的姓名"
git config --global user.email "您的邮箱"
```

### 验证配置
```bash
git config --list
```

## 常见问题

1. **安装后需要重启终端**：安装完成后，请关闭并重新打开PowerShell
2. **PATH环境变量**：Git安装程序会自动添加到系统PATH中
3. **权限问题**：如果遇到权限问题，请以管理员身份运行安装程序


