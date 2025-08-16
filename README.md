# mcp-scraper
网页内容抓取工具

## 核心功能
- 自动提取网页文章内容和元数据
- 双模式抓取：直接下载与浏览器渲染
- 支持批量并发抓取，可配置并发数
- 内置反爬虫检测绕过机制
- 智能资源阻断提高抓取效率
- 支持多语言内容检测
- 自动重试与错误处理
- MCP服务器集成

## 技术栈
- Scrapling 用于网页抓取
- Playwright 用于浏览器渲染
- 异步IO实现高效抓取

### 解析 doc 文件

```bash
# ubuntu
sudo apt-get install libreoffice

# mac
brew install libreoffice
```


### pdf 中表格与图片的提取 (效果不佳)

```bash
pip install hf_xet pdf2image

# ubuntu
apt-get install poppler-utils

# mac
brew install poppler
```



## 待解决

- 下载链接由js生成
```
访问: https://egrul.nalog.ru/index.html?t=1747108095816
搜索: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "АЗИЯ ЛАЙФ"
点击搜索出的链接下载
```