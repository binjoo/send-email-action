# Send Email Action (Python)

基于 SMTP 协议发送邮件的 GitHub Action，使用 Python 标准库实现，以 Docker 方式运行。

## 参数说明

### 输入参数

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `smtp_host` | 是 | - | SMTP 服务器地址|
| `smtp_port` | 否 | `465` | SMTP 服务端口 |
| `smtp_username` | 是 | - | SMTP 登录账号 |
| `smtp_password` | 是 | - | SMTP 登录密码 |
| `to` | 是 | - | 收件人地址，多个以逗号 / 分号 / 换行分隔 |
| `cc` | 否 | - | 抄送地址，分隔方式同 `to` |
| `bcc` | 否 | - | 密送地址（不显示于邮件头），分隔方式同 `to` |
| `from` | 视情况 | - | 发件人地址。`smtp_username` 为邮箱地址时默认取该值，否则必填 |
| `sender` | 否 | - | 发件人显示名称 |
| `subject` | 是 | - | 邮件主题 |
| `body` | 是 | - | 邮件正文，支持单行或多行文本 |
| `content_type` | 否 | `text/plain` | 正文格式：`text/plain` 或 `text/html` |
| `attachments` | 否 | - | 附件路径或 glob 通配符，多个以逗号 / 分号 / 换行分隔 |
| `secure` | 否 | `auto` | 加密方式：`auto`（465 端口使用 SSL，其余使用 STARTTLS）/ `ssl` / `starttls` / `none` |

### 输出参数

| 参数 | 说明 |
| --- | --- |
| `message_id` | 已发送邮件的 Message-ID |

## 使用示例

### 简单发送

```yaml
- name: Send email
  uses: binjoo/send-email-action@v1
  with:
    smtp_host: smtp.qq.com
    smtp_username: ${{ secrets.SMTP_USERNAME }}
    smtp_password: ${{ secrets.SMTP_PASSWORD }}
    to: 'dev@example.com'
    subject: '构建通知'
    body: '构建已完成。'
```

### HTML 发送

```yaml
- name: Send HTML email
  uses: binjoo/send-email-action@v1
  with:
    smtp_host: smtp.qq.com
    smtp_username: ${{ secrets.SMTP_USERNAME }}
    smtp_password: ${{ secrets.SMTP_PASSWORD }}
    to: 'dev@example.com'
    subject: '发布报告'
    content_type: text/html
    body: |
      <h2>发布成功</h2>
      <p>版本：<b>${{ github.ref_name }}</b></p>
```

### 带附件发送

```yaml
- name: Send email with attachments
  uses: binjoo/send-email-action@v1
  with:
    smtp_host: smtp.qq.com
    smtp_username: ${{ secrets.SMTP_USERNAME }}
    smtp_password: ${{ secrets.SMTP_PASSWORD }}
    to: 'dev@example.com'
    subject: '构建产物'
    body: '构建产物详见附件。'
    attachments: |
      dist/*.zip
      build/reports/report.html
```
