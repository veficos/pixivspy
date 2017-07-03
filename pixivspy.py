# coding=utf-8
# author=veficos

import pixivspy
import logging
import os
import sys

try:
    import simplejson as json
except ImportError:
    import json


def __make_logger(level, log_path):
    log_dir = os.path.dirname(log_path)
    if log_dir and (not os.path.exists(log_dir)):
        os.makedirs(log_dir)

    __stream_handler = logging.StreamHandler()
    __stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    __stream_handler.setLevel(level)

    __file_handler = logging.FileHandler(configs['log']['path'])
    __file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    __file_handler.setLevel(level)

    logging.basicConfig(level=level,
                        handlers=[
                            __stream_handler,
                            __file_handler,
                        ])


if __name__ == '__main__':
    with open('configs.json', 'r') as fp:
        configs = json.load(fp)

    if not configs:
        print("找不到配置文件...")
        sys.exit(-1)

    __make_logger(configs['log']['level'], configs['log']['path'])

    spy = pixivspy.PixivSpy(path_rule=configs['spy']['path_rule'],
                            file_name_rule=configs['spy']['image_name_rule'],
                            retry=configs['spy']['retry'],
                            timeout=configs['spy']['timeout'],
                            download_timeout=configs['spy']['download_timeout'],
                            rest=configs['spy']['rest'],
                            thread_pool_size=configs['spy']['thread_pool_size'])

    if not spy.login(configs['username'], configs['password']):
        sys.exit(-1)

    if configs['mode'] == 'id':
        logging.info('下载模式: [id]')
        for member_id in configs['id']:
            logging.info('准备下载图集：[member_id: %s]' % (member_id, ))
            spy.download_member_illusts(member_id)

    elif configs['mode'] == 'star':
        logging.info('下载模式: [star]')
        for member_id in configs['id']:
            logging.info('待下载的关注列表: [member_id: %s]' % (member_id,))
            spy.download_star_illust(member_id)

    else:
        print('未知的下载模式\n')
        sys.exit(-1)
