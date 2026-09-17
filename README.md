# Send Email Action (Python)

通过 SMTP 发送邮件的 GitHub Action，使用 **Python 标准库** 实现（零第三方依赖），以 Docker 方式运行。

支持：

- ✅ SMTP 服务器信息：`smtp_host` / `smtp_port` / `smtp_username` / `smtp_password`
- ✅ **多个收件人**（逗号、分号或换行分隔），另支持 `cc` / `bcc`
- ✅ 邮件标题、**单行或多行正文**，可选 `text/html` 格式
- ✅ **多个附件**（直接列路径或 glob 通配符）
- ✅ 自动 TLS：465 端口走 SSL，其他端口走 STARTTLS（可用 `secure` 强制指定）

## 使用示例

```yaml
name: Notify

on:
  workflow_dispatch:
  push:
    tags: ['v*']

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Send email
        uses: binjoo/send-email-action@v1
        with:
          smtp_host: smtp.qq.com
          smtp_port: 465
          smtp_username: ${{ secrets.SMTP_USERNAME }}
          smtp_password: ${{ secrets.SMTP_PASSWORD }}
          sender: 'CI 机器人'
          to: 'dev@example.com, ops@example.com'   # 多个收件人
          cc: 'boss@example.com'
          subject: '构建通知：${{ github.repository }}'
          body: |                                   # 多行正文
            构建完成 ✅
            仓库：${{ github.repository }}
            分支：${{ github.ref_name }}
            提交：${{ github.sha }}
          attachments: |                            # 多个附件（支持通配符）
            dist/*.zip
            build/reports/report.html
```

### HTML 邮件

```yaml
      - name: Send HTML email
        uses: binjoo/send-email-action@v1
        with:
          smtp_host: smtp.example.com
          smtp_username: ${{ secrets.SMTP_USERNAME }}
          smtp_password: ${{ secrets.SMTP_PASSWORD }}
          to: 'dev@example.com'
          subject: '发布报告'
          content_type: text/html
          body: |
            <h2>发布成功</h2>
            <p>版本：<b>${{ github.ref_name }}</b></p>
```

### 多个附件（路径列表 / 通配符）

```yaml
          attachments: |          # 每行一个，支持 glob 通配符，匹配到的文件自动展开
            dist/*.zip
            build/reports/report.html
```

也可以写在同一行，用逗号分隔：`attachments: 'dist/*.zip, README.md'`

## 输入参数

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `smtp_host` | 是 | - | SMTP 服务器地址，如 `smtp.qq.com`、`smtp.163.com`、`smtp.gmail.com` |
| `smtp_port` | 否 | `465` | SMTP 端口 |
| `smtp_username` | 是 | - | SMTP 登录用户名（通常是发件邮箱） |
| `smtp_password` | 是 | - | SMTP 密码或授权码，**务必通过 `secrets` 传入** |
| `to` | 是 | - | 收件人，多个用逗号 / 分号 / 换行分隔 |
| `cc` | 否 | - | 抄送，分隔方式同 `to` |
| `bcc` | 否 | - | 密送（不会出现在邮件头中），分隔方式同 `to` |
| `from` | 否 | `username` | 发件人地址（某些服务商要求与登录账号一致） |
| `sender` | 否 | - | 发件人显示名称，如 `CI Bot` |
| `subject` | 是 | - | 邮件标题 |
| `body` | 是 | - | 邮件正文，支持单行或多行文本 |
| `content_type` | 否 | `text/plain` | `text/plain` 或 `text/html` |
| `attachments` | 否 | - | 附件：换行/逗号分隔的路径或 glob 通配符，多个自动展开 |
| `secure` | 否 | `auto` | `auto`（465 走 SSL，其余走 STARTTLS）/ `ssl` / `starttls` / `none` |

## 输出

| 输出 | 说明 |
| --- | --- |
| `message_id` | 已发送邮件的 Message-ID |

## 注意事项

- **密码安全**：`password` 一定要用 GitHub Secrets，不要明文写在 workflow 里。
- **授权码**：QQ 邮箱、163 邮箱、Gmail 等需要在邮箱设置中开启 SMTP 并生成"授权码 / 应用专用密码"，不能用网页登录密码。
- **运行环境**：本 Action 以 Docker 方式运行，仅支持 `ubuntu-latest` 等 Linux runner。
- **超时**：SMTP 连接内置 60 秒超时，避免挂死整个 job。

## 本地开发

实现只依赖 Python 标准库（`smtplib` / `email` / `ssl` 等），无 `requirements.txt`。本地调试：

```bash
# 直接用环境变量模拟 GitHub runner 注入的 INPUT_* 变量
INPUT_SMTP_HOST=smtp.qq.com INPUT_SMTP_PORT=465 \
INPUT_SMTP_USERNAME=you@example.com INPUT_SMTP_PASSWORD=xxx \
INPUT_TO='a@example.com, b@example.com' \
INPUT_SUBJECT=hello INPUT_BODY='line1
line2' \
INPUT_ATTACHMENTS='dist/*.zip, README.md' \
python main.py
```

## 项目结构

```
send-email-action/
├── action.yml    # Action 元数据与参数定义（Docker 方式运行）
├── main.py       # Python 实现（纯标准库）
├── Dockerfile    # python:3.12-slim，无第三方依赖
└── README.md
```
