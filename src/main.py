#!/usr/bin/python3
import ins
import db


# 主程序，脚本通过 crontab 每半个小时运行一次，增量添加新帖子数据到 db

# 打开 db 连接，顺便初始化表
conn = db.init_conn()

# 循环获取关注人的 ins 帖子
for url in ins.ins_url_list:
    # 获取主页 html
    html = ins.get_ins_data(url)
    if html == '':
        print('url: ' + url + ", request error")
        continue

    # 解析得到帖子列表第一页数据
    post_info = ins.parse_home_page(html)

    # 查询 db，获取该博主的最近爬取的一条帖子记录
    conn = db.init_conn()
    res_list = db.select_last_post(conn, post_info['id'])

    # 爬取所有帖子的功能暂时屏蔽
    # if len(res_list) == 0:
    #     # 获取所有帖子并插入数据库
    #     post_info = ins.get_ins_posts(post_info, -1, -1)
    # else:
    #     # 对比最新数据，判断有多少新帖子需要获取并插入
    #     last_post = res_list[0]
    #     new_posts = []
    #     for post in post_info['posts']:
    #         if post['taken_at_timestamp'] > last_post['taken_at_timestamp'] and int(post['id']) \
    #                 > last_post['id']:
    #             new_posts.append(post)
    #     # 需要加载更多帖子确定新帖子的数量
    #     if len(new_posts) == len(post_info['posts']):
    #         post_info = ins.get_ins_posts(post_info, last_post['id'],
    #                                       last_post['taken_at_timestamp'])
    #     else:
    #         post_info['posts'] = new_posts
    # print('get new posts for %s, length: %s' % (post_info['name'], str(len(post_info['posts']))))

    # 初始只爬取最近 10 条，之后爬取初始 10 条后的新帖子
    if len(res_list) == 0:
        # 获取前 10
        if len(post_info['posts']) > 10:
            post_info['posts'] = post_info['posts'][0:10]
    else:
        # 对比最新数据，判断有多少新帖子需要获取并插入
        last_post_id = res_list[0][0]
        last_post_timestamp = res_list[0][5]
        new_posts = []
        for post in post_info['posts']:
            if post['taken_at_timestamp'] > last_post_timestamp and int(post['id']) > last_post_id:
                new_posts.append(post)
        # 首页的帖子都是新帖子，需要加载更多帖子确定新帖子的数量
        if len(new_posts) == len(post_info['posts']):
            post_info = ins.get_ins_posts(post_info, last_post_id, last_post_timestamp)
        else:
            post_info['posts'] = new_posts
    print('get new posts for %s, length: %s' % (post_info['name'], str(len(post_info['posts']))))

    # 获取新帖子的详细媒体
    post_info['posts'] = ins.get_post_details(post_info['posts'])
    print('get new posts for ' + post_info['name'] + ', details done')

    # 插入数据库
    db.insert_new_posts(conn, post_info['posts'])
    print('inserted done')

# 关闭 db 连接
db.close_conn(conn)
