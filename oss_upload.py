# -*- coding: utf-8 -*-

from __future__ import division
from datetime import timedelta, datetime

import os
import random
import string
import oss2
import math
import sys

# 设置一: 打包并上传的文件

# 1、文件路劲
file_path = "/data/syslog-ng/network/"
# 2、当前时间前一天 目录格式如: /data/syslog-ng/network/20180725
file_time = (datetime.today() + timedelta(-1)).strftime('%Y%m%d')
file_name = "%s.tar.gz" % file_time
# 3、系统打包命令
os.system("cd {0} && tar -cvzf {1} {2} --remove-files".format(file_path, file_name, file_time))


# 设置二: 阿里云账号

# 1、阿里账号access_key_id
my_access_key_id = "1PJmSBnqLGE6r1M"
# 2、阿里账号access_key_secret
my_access_key_secret = "KF2rNToaHjstAfFNxU6gAyQoQ3q16"
# 3、oss bucket名
my_bucket_name = "lilongz"
# 4、bucket域名
my_endpoint = "http://oss-cn-hangzhou.aliyuncs.com"


# 检查打包是否成功
filename = "%s%s" % (file_path, file_name)
if not os.path.exists(filename):
    print "File Not Found..%s" % filename
    sys.exit()

access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', my_access_key_id)
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', my_access_key_secret)
bucket_name = os.getenv('OSS_TEST_BUCKET', my_bucket_name)
endpoint = os.getenv('OSS_TEST_ENDPOINT', my_endpoint)

# 请求参数
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param

# 创建Bucket对象
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

# 设定分片大小为128KB
total_size = os.path.getsize(filename)
part_size = oss2.determine_part_size(total_size, preferred_size=128 * 1024)

# 初始化分片上传，得到Upload ID
upload_id = bucket.init_multipart_upload(file_name).upload_id


def progressbar(cur, total):
    """ 进度条 """
    percent = '{:.2%}'.format(cur / total)
    sys.stdout.write('\r')
    sys.stdout.write('[%-50s] %s' % ('=' * int(math.floor(cur * 50 / total)), percent))
    sys.stdout.flush()
    if cur == total:
        sys.stdout.write('\n')


# 逐个上传分片
print "Upload %s to %s %s..." % (filename, my_endpoint, my_bucket_name)
with open(filename, 'rb') as fileobj:
    parts = []
    part_number = 1
    offset = 0
    while offset < total_size:
        num_to_upload = min(part_size, total_size - offset)
        result = bucket.upload_part(file_name, upload_id, part_number,
                                    oss2.SizedFileAdapter(fileobj, num_to_upload))
        parts.append(oss2.models.PartInfo(part_number, result.etag))

        offset += num_to_upload
        part_number += 1

        progressbar(offset * 10 / total_size, 10)

    # 完成分片上传
    bucket.complete_multipart_upload(file_name, upload_id, parts)


