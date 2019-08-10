# InsToWeibo

Ins 搬运工计划

*佛系开发，慢慢来，python 也是现学的*

项目源于喜欢上韩国艺人 IU，发现微博关于她的内容很少，所以萌生将 ins 上 iu 官方账户和大量 iu 相关资讯账户的帖子爬下来，并自动发布到微博上。

**有 IU 粉丝提醒，搬运功能可能会触动到粉丝站的利益。**

### 完成内容

* ins 帖子爬取并存储到 splite db 中，支持增量爬取，不爬取重复数据

### 存在问题

* 考虑到爬取的旧帖子数量过多，ins 接口时不时有返回失败的情况，一方面加上休眠时间间隔，另一方面每个账户的初始爬取帖子数量限定为最新 10 条，之后增量爬取初始 10 条后的所有新帖子

* 微博登录和发微博最好通过模拟请求来实现，官方 API 太麻烦，要求过多，有些功能只能企业账号才能接入

### 如何使用

Read the code, and you will know!

那我是建议用 IntelliJ IDEA 或者 PyCharm 咯，爬完还可以可视化查看 db。

```
cd src && python3 main.py
```