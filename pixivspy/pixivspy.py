# coding=utf-8
# author=veficos


try:
    import simplejson as json
except ImportError:
    import json

import requests
import pyquery
import logging
import re
import os
import time

from concurrent.futures import ThreadPoolExecutor

from .configs import pixiv_urls
from .configs import pixiv_login_headers
from .configs import pixiv_html_headers
from .configs import pixiv_image_headers
from .utils import RetryExecute, retry_execute


class PixivSpy(object):

    def __init__(self,
                 path_rule='{member_name}',
                 file_name_rule='{image_pname}',
                 retry=10,
                 timeout=60,
                 download_timeout=120,
                 resttime=1,
                 thread_pool_size=10,
                 *args,
                 **kwargs):

        self.path_rule = path_rule
        self.file_name_rule = file_name_rule

        self.retry = retry
        self.timeout = timeout
        self.resttime = resttime
        self.download_timeout = download_timeout

        self.session = requests.session()
        self.thread_pool_size = thread_pool_size

        self.logined = False

    def __get_post_key(self, html_doc):
        pq = pyquery.PyQuery(html_doc)
        input_tags = pq.find('input')
        for input_tag in input_tags:
            if input_tag.name == 'post_key':
                return input_tag.value
        return None

    def __proxy_post(self, url, headers=None, data=None, timeout=None):
        try:
            headers = pixiv_html_headers if headers is None else headers
            data = {} if data is None else data
            timeout = self.timeout if timeout is None else timeout
            return self.session.post(url, headers=headers, data=data, timeout=timeout)
        except Exception as e:
            logging.warning('请求POST失败: [url: %s][header: %s][data: %s][timeout: %s][error: %s]' %
                            (url, headers, data, timeout, e))
            raise RetryExecute()

    def proxy_post(self, url, headers=None, data=None, timeout=None):
        return retry_execute(self.retry)(self.__proxy_post)(url, headers, data, timeout)

    def __proxy_get(self, url, headers=None, data=None, timeout=None):
        try:
            headers = pixiv_html_headers if headers is None else headers
            data = {} if data is None else data
            timeout = self.timeout if timeout is None else timeout
            return self.session.get(url, headers=headers, data=data, timeout=timeout)
        except Exception as e:
            logging.warning('请求GET失败: [url: %s][header: %s][data: %s][timeout: %s][error: %s]' %
                            (url, headers, data, timeout, e))
            raise RetryExecute()

    def proxy_get(self, url, headers=None, data=None, timeout=None):
        return retry_execute(self.retry)(self.__proxy_get)(url, headers, data, timeout)

    def login(self, username, password):
        """ 登陆pixiv """
        try:
            logging.info('正在登录pixiv: [用户名: %s]' % (username, ))

            r = self.proxy_get(pixiv_urls['pre_login'],
                               headers=pixiv_login_headers,
                               timeout=self.timeout)

            postkey = self.__get_post_key(r.text)

            r = self.proxy_post(pixiv_urls['act_login'], data={
                'pixiv_id': username,
                'password': password,
                'post_key': postkey,
                'source': 'accounts'
            })

            doc = json.loads(r.text)

            if doc['error']:
                self.logined = True
                logging.info('登录pixiv成功: [用户名: %s]' % (username,))

            return not doc['error']
        except Exception as e:
            logging.warning('登陆Pixiv失败: [error: %s]' % (e,), exc_info=True)

        return False

    def logout(self):
        """ 退出登陆 """
        if self.logined:
            self.session.close()
            self.logined = False

    def get_star_members(self, member_id=None):
        """ 获取member_id关注的member_id """
        stars = []
        index = 1

        try:
            url = pixiv_urls['star'] + (('&id=%s' % (member_id, )) if member_id is None else '')

            while True:
                star_url = url + '&p=%s' % index

                """ 获取关注页面 """
                r = self.proxy_get(star_url)
                if not r:
                    break

                pq = pyquery.PyQuery(r.text)

                member_items = pq.find('div.userdata')

                if not len(member_items):
                    break

                for member_item in member_items:
                    stars.append(member_item.find('a').attrib['data-user_id'])

                index += 1

        except Exception as e:
            logging.warning('获取所有关注用户失败: [member_id: %s][error: %s]' % (member_id, e))

        return stars

    def get_member_page(self, member_id, index=1):
        """ 获取member_id的主页 """
        try:
            logging.info('正在获取P主主页: [member_id: %s][index: %s]' % (member_id, index))

            r = self.proxy_get(pixiv_urls['member'].format(member_id=member_id, index=index))

            return r.text
        except Exception as e:
            logging.warning('获取P主主页失败: [error: %s][member_id: %s][index: %s]' % (e, member_id, index), exc_info=True)

        return ''

    def get_member_name_by_member_id(self, member_id):
        """ 获取member_id的昵称 """
        try:
            page = self.get_member_page(member_id)
            if not page:
                return ''

            pq = pyquery.PyQuery(page)
            user = pq.find('h1.user')

            return user.text() if user else 'unknown'
        except Exception as e:
            logging.warning('获取P主昵称失败: [error: %s][member_id: %s]' % (e, member_id), exc_info=True)

        return ''

    def get_star_user_total(self, member_id):
        """ 获取关注用户数量 """
        try:
            url = pixiv_urls['star'] + (('&id=%s' % (member_id, )) if member_id else '')

            r = self.proxy_get(url)

            pq = pyquery.PyQuery(r.text)

            return int(pq.find('.count-badge').text())
        except Exception as e:
            logging.warning('获取关注用户总量失败: [error: %s][member_id: %s]' % (e, member_id), exc_info=True)

        return 0

    def get_illust_images(self, illust_id, title, multiple):
        """ 获取图集所有图片 """
        if multiple:
            return self.get_multiple_illust_images(illust_id, title)
        else:
            return self.get_single_illust_images(illust_id, title)

    def get_single_illust_images(self, illust_id, title):
        """ 获取单张图片的图集 """
        images = []

        try:
            r = self.proxy_get(pixiv_urls['single_illust'].format(illust_id=illust_id))

            pq = pyquery.PyQuery(r.text)

            image_items = pq.find('.original-image')

            for image_item in image_items:
                images.append({
                    'url': image_item.attrib['data-src'],
                    'title': image_item.attrib['alt'],
                    'width': image_item.attrib['width'],
                    'height': image_item.attrib['height'],
                })

            return images

        except Exception as e:
            logging.warning('解析单张图片图集失败: [title: %s][error: %s]' % (title, e), exc_info=True)

        return images

    def get_multiple_illust_images(self, illust_id, title):
        """ 获取多张图片的图集 """
        images = []

        def get_multiple_illust_count(get, illust_id):
            try:
                r = get(pixiv_urls['multiple_illust'].format(illust_id=illust_id))

                pq = pyquery.PyQuery(r.text)

                return len(pq.find('.item-container'))
            except Exception as e:
                logging.warning('获取图集数量失败: [illust_id: %s][error: %s]' % (illust_id, e), exc_info=True)

            return 0

        def get_images(get, index):
            nonlocal images
            try:
                logging.info('正在解析多张图片图集: [title: %s]' % (title, ))

                r = get(pixiv_urls['multiple_illust_image'].format(illust_id=illust_id, index=index))

                pq = pyquery.PyQuery(r.text)

                images.append({
                    'url': pq.find('body img').attr('src'),
                    'title': title + '_' + str(index),
                    'width': '0',
                    'height': '0',
                })

                return True

            except Exception as e:
                logging.warning('解析多张图片图集失败: [title: %s][error: %s]' % (title, e), exc_info=True)

            return False

        for index in range(get_multiple_illust_count(self.proxy_get, illust_id)):
            if not get_images(self.proxy_get, index):
                break

        return images

    def get_member_illusts(self, member_id):
        """ 获取P主所有图片集 """
        illusts = []
        index = 1
        fault = 1
        illust_id_pattern = re.compile(r'(?<=illust_id=).*')
        illust_multiple_pattern = re.compile(r'multiple')

        try:
            while True:
                page = self.get_member_page(member_id, index)

                if page:
                    logging.info('准备解析[%s]P主第[%s]页作品' % (member_id, index))

                    pq = pyquery.PyQuery(page)

                    work_items = pq.find('a.work')
                    if not len(work_items):
                        logging.info('已访问到[%s]P主最后一页图集' % (member_id, ))
                        return illusts

                    illust_name_items = pq.find('a h1.title')

                    for i, work_item in enumerate(work_items):
                        _href = work_item.attrib['href']
                        _class = work_item.attrib['class']
                        _illust_id_match = illust_id_pattern.search(_href)
                        if _illust_id_match:
                            begin, end = _illust_id_match.span()
                            _illust_id = _href[begin: end]
                        else:
                            _illust_id = ''

                        illusts.append({
                            'href': _href,
                            'multiple': True if illust_multiple_pattern.findall(_class) else False,
                            'title': illust_name_items.eq(i).text(),
                            'id': _illust_id
                        })

                    index += 1
                else:
                    logging.warning('访问P主主页失败: [member_id: %s][index: %s]' % (member_id, index), exc_info=True)

        except Exception as e:
            if fault > 5:
                return illusts
            logging.warning('获取P主所有图片集失败:[member_id: %s][fault: %s][error: %s]' % (member_id, fault, e), exc_info=True)
            fault += 1

        return illusts

    def download_member_illusts(self, member_id):
        """ 下载P主的所有图集 """
        try:
            member_name = self.get_member_name_by_member_id(member_id)

            illusts = self.get_member_illusts(member_id)

            illust_thread_pool = ThreadPoolExecutor(self.thread_pool_size)

            for illust in illusts:
                images = self.get_illust_images(illust['id'], illust['title'], illust['multiple'])
                for image in images:
                    def thread_task():
                        self.download_image(member_name=member_name,
                                            member_id=member_id,
                                            illust_name=illust['title'],
                                            illust_id=illust['id'],
                                            image_name=image['title'],
                                            image_width=image['width'],
                                            image_height=image['height'],
                                            url=image['url'])

                        time.sleep(self.resttime)

                    illust_thread_pool.submit(thread_task)

            illust_thread_pool.shutdown()

        except Exception as e:
            logging.warning('下载P主的所有图集失败: [error: %s][member_id: %s]' % (e, member_id), exc_info=True)

    def download_star_illust(self, member_id):
        """ 下载member_id关注列表用户的所有图集 """
        star_member_ids = self.get_star_members(member_id)

        logging.info('获取到关注用户: [members: %s]' % (star_member_ids,))

        for star_member_id in star_member_ids:
            self.download_member_illusts(star_member_id)

    def download_image(self, member_name, member_id,
                       illust_name, illust_id,
                       image_name, image_width, image_height, url):
        """ 下载图片 """
        try:
            path = self.path_rule.format(member_name=member_name,
                                         member_id=member_id,
                                         illust_name=illust_name,
                                         illust_id=illust_id,
                                         image_name=image_name,
                                         image_width=image_width,
                                         image_height=image_height,
                                         time=int(time.time() * 100000))

            file_name = self.file_name_rule.format(member_name=member_name,
                                                   member_id=member_id,
                                                   illust_name=illust_name,
                                                   illust_id=illust_id,
                                                   image_name=image_name,
                                                   image_width=image_width,
                                                   image_height=image_height,
                                                   image_pname=os.path.basename(url),
                                                   time=int(time.time() * 100000))

            extension = '' if os.path.splitext(file_name)[-1:][0] else os.path.splitext(url)[-1:][0]

            if not os.path.exists(path):
                logging.info('新建目录: [path: %s]' % (path, ))
                os.makedirs(path)

            save_to = os.path.join(path, file_name + extension)
            if os.path.exists(save_to):
                logging.info('图片已存在: [save_to: %s][url: %s]' % (save_to, url))
                return

            logging.info('正在下载图片: [url: %s]' % (url, ))

            r = self.proxy_get(url,
                               headers=dict(pixiv_image_headers, Referer=url),
                               timeout=self.download_timeout)

            if r:
                with open(save_to, 'wb') as fp:
                    fp.write(r.content)
                    logging.info('图片下载完成: [file: %s][url: %s]' % (save_to, url))

        except Exception as e:
            logging.warning('图片下载失败: [url: %s][error: %s]' % (url, e), exc_info=True)
