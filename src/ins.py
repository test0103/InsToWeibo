#!/usr/bin/python3
import json
import time

import requests
from pyquery import PyQuery
import re
from urllib import parse

ins_url_list = [
    'https://www.instagram.com/dlwlrma/',
    # 'https://www.instagram.com/iu_leejieun516/',
    # 'https://www.instagram.com/fullmoon.long/'
]
csrf_token = ''


# 请求 ins 数据
def get_ins_data(url):
    # 代理，看情况自行处理
    proxies = {"http": "127.0.0.1:1087", "https": "127.0.0.1:1087"}
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, '
                      'like Gecko) Chrome/75.0.3770.142 Safari/537.36',
    }
    if len(csrf_token) > 0:
        headers['x-csrftoken'] = csrf_token

    try:
        response = requests.get(url, headers=headers, proxies=proxies)
        if response.status_code == 200:
            return response.text
        else:
            print('url: ' + url + ", code: " + response.status_code)
            return ''
    except Exception as e:
        print(e)
        return ''


# 解析帖子列表
def parse_posts(edges, poster_id, poster_username):
    posts = []
    for edge in edges:
        post = {'id': edge['node']['id'], 'shortcode': edge['node']['shortcode'],
                'is_video': edge['node']['is_video'], 'poster_id': poster_id,
                'taken_at_timestamp': edge['node']['taken_at_timestamp'],
                'data': {}, 'post_to_weibo': 0, 'poster_username': poster_username}
        posts.append(post)
    return posts


# 解析 html
def parse_home_page(html):
    posts_info = {}
    doc = PyQuery(html)
    items = doc('script[type="text/javascript"]').items()
    for item in items:
        # 拿到 queryId，即分页请求的 query_hash
        if type(item.attr('src')) is str and str(item.attr('src')).find(
                "ProfilePageContainer.js") != -1:
            profile_js = get_ins_data('https://www.instagram.com' + str(item.attr('src')))
            search_result = re.search('__d(.*?)edge_owner_to_timeline_media(.*?)', profile_js)
            if search_result:
                search_result = re.search('queryId:"(.*)"', search_result.group(0))
                if search_result:
                    posts_info['quert_hash'] = search_result.group(1)

        # 拿到第一页的帖子数据和 end_cursor，即分页请求的 after 参数
        if item.text().strip().startswith('window._sharedData'):
            json_data = json.loads(item.text()[21:-1], encoding='utf-8')
            global csrf_token
            csrf_token = json_data['config']['csrf_token']
            posts_info['id'] = json_data['entry_data']['ProfilePage'][0]['graphql']['user']['id']
            posts_info['name'] = json_data['entry_data']['ProfilePage'][0]['graphql']['user'][
                'username']
            edges = json_data['entry_data']['ProfilePage'][0]['graphql']['user'][
                'edge_owner_to_timeline_media']['edges']
            posts_info['posts'] = parse_posts(edges, posts_info['id'], posts_info['name'])
            page_info = json_data['entry_data']['ProfilePage'][0]['graphql']['user'][
                'edge_owner_to_timeline_media']['page_info']
            posts_info['end_cursor'] = page_info['end_cursor']
            posts_info['has_next_page'] = page_info['has_next_page']
    return posts_info


# 分页请求所有帖子
def get_ins_posts(posts_info, last_post_id, last_post_timstamp):
    while posts_info['has_next_page']:
        time.sleep(2)
        variables = {'id': posts_info['id'], 'first': 50, 'after': posts_info['end_cursor']}
        query_url = 'https://www.instagram.com/graphql/query/?query_hash=' + posts_info[
            'quert_hash'] + "&variables=" + parse.quote(str(json.dumps(variables)))
        data = get_ins_data(query_url)
        if data:
            json_data = json.loads(data)
            edges = json_data['data']['user']['edge_owner_to_timeline_media']['edges']
            ins_posts = parse_posts(edges, posts_info['id'], posts_info['name'])
            new_posts = []
            load_next_page = True
            for post in ins_posts:
                if post['taken_at_timestamp'] > last_post_timstamp and int(post['id']) > \
                        last_post_id:
                    new_posts.append(post)
            if len(new_posts) < len(ins_posts):
                load_next_page = False
            posts_info['posts'].extend(new_posts)
            page_info = json_data['data']['user']['edge_owner_to_timeline_media']['page_info']
            posts_info['end_cursor'] = page_info['end_cursor']
            posts_info['has_next_page'] = page_info['has_next_page'] and load_next_page
        else:
            posts_info['has_next_page'] = False
    # print(json.dumps(posts_info))
    return posts_info


# 解析单张图片数据
def parse_single_image_data(resources):
    single_data = {}
    min_width = -1
    max_width = -1
    for item in resources:
        if min_width == -1 or min_width > item['config_width']:
            min_width = item['config_width']
            single_data['thumbnail_url'] = item['src']
        if max_width == -1 or max_width < item['config_width']:
            max_width = item['config_width']
            single_data['image_url'] = item['src']
    return single_data


# 请求帖子详情
def get_post_details(posts):
    for post in posts:
        time.sleep(2)
        post_url = 'https://www.instagram.com/p/' + post['shortcode'] + '/'
        print('begin request post: ' + post_url)
        html = get_ins_data(post_url)
        if html == '':
            print('url: ' + post_url + ", request error")
            continue
        doc = PyQuery(html)
        items = doc('script[type="text/javascript"]').items()
        for item in items:
            if item.text().strip().startswith('window._sharedData'):
                json_data = json.loads(item.text()[21:-1], encoding='utf-8')
                media = json_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']
                # 帖子展示缩略图
                single_data = parse_single_image_data(media['display_resources'])
                data = {'thumbnail_url': single_data['thumbnail_url']}
                # 文字描述
                if len(media['edge_media_to_caption']['edges']) > 0:
                    data['text'] = media['edge_media_to_caption']['edges'][0]['node']['text']
                # 视频
                if media['is_video']:
                    post['is_video'] = True
                    data['video_url'] = media['video_url']
                # 图片
                else:
                    post['is_video'] = False
                    data['image_list'] = []
                    # 多张图片
                    if hasattr(media, 'edge_sidecar_to_children'):
                        edges = media['edge_sidecar_to_children']['edges']
                        for edgeItem in edges:
                            data['image_list'].append(parse_single_image_data(
                                edgeItem['node']['display_resources']))
                    # 单张图片
                    else:
                        data['image_list'].append(single_data)
                post['data'] = data
    return posts
