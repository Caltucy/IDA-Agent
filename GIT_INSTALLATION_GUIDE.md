# Git安装指南

## 方法1：使用winget（推荐）

### 自动安装
```powershell
# 同意协议并安装
winget install Git.Git --accept-source-agreements --accept-package-agreements
```

### 手动确认安装
```powershell
# 运行此命令，然后按Y同意协议
winget install Git.Git
```

## 方法2：手动下载安装（最可靠）

### 步骤：
1. 访问 [Git官网下载页面](https://git-scm.com/download/win)
2. 下载最新版本的Git for Windows（约60MB）
3. 运行下载的安装程序
4. 使用默认设置安装（推荐）
5. 安装完成后重启PowerShell

### 安装选项说明：
- ✅ 添加到PATH环境变量
- ✅ 使用Git Bash和Git GUI
- ✅ 使用Windows命令提示符
- ✅ 使用Windows PowerShell
- ✅ 使用Visual Studio Code

## 方法3：使用Chocolatey（如果已安装）

```powershell
# 检查是否已安装Chocolatey
choco --version

# 如果已安装，运行：
choco install git
```

## 方法4：使用Scoop（如果已安装）

```powershell
# 检查是否已安装Scoop
scoop --version

# 如果已安装，运行：
scoop install git
```

## 安装后验证

安装完成后，重启PowerShell并运行：
```powershell
git --version
```

如果显示版本号，说明安装成功。

## 配置Git（可选）

安装完成后，建议配置用户信息：
```powershell
git config --global user.name "您的姓名"
git config --global user.email "您的邮箱"
```

## 故障排除

### 如果安装后仍无法使用Git：
1. 重启PowerShell或命令提示符
2. 检查PATH环境变量是否包含Git路径
3. 尝试重启计算机

### 如果winget安装失败：
- 使用手动下载安装（方法2）
- 确保网络连接正常
- 以管理员身份运行PowerShell

## 推荐方案
**建议使用方法2（手动下载安装）**，因为：
- 最可靠，不会因为网络问题中断
- 可以自定义安装选项
- 适合所有Windows版本


