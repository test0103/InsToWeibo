#!/usr/bin/python3
import json
import os
import sqlite3


# 初始化 db 连接，并判断是否初始化数据表
def init_conn():
    if not os.path.exists('../db'):
        os.mkdir('../db')
    conn = sqlite3.connect('../db/ins.db')
    # create db
    cursor = conn.cursor()
    cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'ins_post'")
    if cursor.fetchall()[0][0] == 0:
        cursor.execute('''create table ins_post(
        post_id long primary key not null,
        shortcode varchar not null,
        poster_id long not null,
        poster_username varchar not null,
        is_video boolean not null,
        taken_at_timestamp long not null,
        data varchar not null,
        post_to_weibo int not null)
        ''')
        conn.commit()
    cursor.close()
    return conn


# 关闭 db 连接
def close_conn(conn):
    conn.close()


# 获取最近爬取的一条帖子数据
def select_last_post(conn, poster_id):
    cursor = conn.cursor()
    cursor.execute('''select * from ins_post where poster_id = {id} order by taken_at_timestamp 
    desc limit 1'''.format(id=poster_id))
    conn.commit()
    res_list = cursor.fetchall()
    cursor.close()
    return res_list


# 插入数据库
def insert_new_posts(conn, posts):
    cursor = conn.cursor()
    for post in posts:
        sql_str = '''insert into ins_post (
        post_id,shortcode,poster_id,poster_username,is_video,taken_at_timestamp,data,post_to_weibo) 
        VALUES ({id},'{code}',{poster_id},'{poster_username}',{is_video},{time},'{data}',{to_weibo})
        '''.format(id=post['id'], code=post['shortcode'], poster_id=post['poster_id'],
                   poster_username=post['poster_username'], is_video=post['is_video'],
                   time=post['taken_at_timestamp'], data=str(json.dumps(post['data'])),
                   to_weibo=post['post_to_weibo'])
        print(sql_str)
        cursor.execute(sql_str)
    conn.commit()
    cursor.close()
