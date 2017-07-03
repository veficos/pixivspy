# coding=utf-8
# author=veficos


pixiv_urls = {
    'pre_login': 'https://accounts.pixiv.net/login',
    'act_login': 'https://accounts.pixiv.net/api/login',

    'home': 'https://www.pixiv.net',
    'login': 'https://www.pixiv.net/login.php',
    'member': 'https://www.pixiv.net/member_illust.php?id={member_id}&type=all&p={index}',
    'single_illust': 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id={illust_id}',
    'multiple_illust': 'https://www.pixiv.net/member_illust.php?mode=manga&illust_id={illust_id}',
    'multiple_illust_image': 'https://www.pixiv.net/member_illust.php?mode=manga_big&illust_id={illust_id}&page={index}',
    'star': 'https://www.pixiv.net/bookmark.php?type=user',
}


pixiv_login_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
    'Connection': 'keep-alive',
    'Host': 'accounts.pixiv.net',
    'Referer': 'http://www.pixiv.net/',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/50.0.2661.102 Safari/537.36'
}

pixiv_html_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept-Encoding': 'gzip,deflate,sdch',
}



pixiv_image_headers = {
    'Accept': 'image/webp,image/*,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept-Encoding': 'gzip,deflate,sdch',
}
