
# 简介

pixiv爬虫

# 使用方式

通过配置config.json控制下载方式，其中主要配置项有

1.下载路径

下载路径由两个配置项组合而成，可以灵活命名。

```
   "path_rule": "D:\\pixiv\\{member_name}"
   "image_name_rule": "{illust_name}_{image_name}_{image_pname}"
```

2.用户名

通过赋值username配置登录用户名，例如

```
   "username": "username"
```

3.用户名密码

通过赋值password配置登录用户名密码，例如

```
   "password": "password"
```

4.下载模式

通过赋值Mode配置下载模式，例如

```
   "mode": "id"
```

目前版本仅支持使用者使用star|id方式下载图片。

当使用star时，IDS表示对应P主的关注页面。如果IDS为空，则爬取自己的关注页

5.P主ID

通过赋值IDS配置想要下载哪些P主的图片集，例如

```
   "id": ["2616777", "6996493"]
```

