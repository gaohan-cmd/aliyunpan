'''
File: autoSign.py
Author: gaohan
Date: 2024/1/14 9:02
cron: 0 30 10 * * *
'''
import sys
import os
import traceback
import requests
from loguru import logger

# 设置日志文件路径
SIGN_LOG = 'logs/aliyunpan.log'
work_path = os.path.dirname(os.path.abspath(__file__))
SIGN_LOG_FILE = os.path.join(work_path, SIGN_LOG)

# 配置logger，添加控制台输出和文件输出
logger.remove()
logger.add(sys.stdout, level='INFO')
logger.add(SIGN_LOG_FILE, encoding='utf8')

# 配置微信推送的用户令牌和Server酱的PUSH_KEY
PUSH_PLUS_TOKEN = os.getenv('PUSH_PLUS_TOKEN', '')
PUSH_KEY = os.getenv('PUSH_KEY', '')

# 配置阿里云盘的refresh_token(JSON.parse(localStorage.getItem("token")).refresh_token控制台输入获取)
refresh_token = os.getenv('aliyunpan_refresh_token')
if refresh_token is None:
    logger.error("请先在环境变量里添加阿里云盘的refresh_token")
    exit(0)

# 函数：发送消息
def post_msg(url: str, data: dict) -> bool:
    response = requests.post(url, data=data)
    code = response.status_code
    return code == 200

# 函数：推送消息到PushPlus
def PushPlus_send(token, title: str, desp: str = '', template: str = 'markdown') -> bool:
    url = 'http://www.pushplus.plus/send'
    data = {
        'token': token,# 用户token
        'title': title,# 消息标题
        'content': desp,# 消息主体内容
        'template': template,
    }
    return post_msg(url, data)

# 函数：推送消息到ServerChan
def ServerChan_send(sendkey, title: str, desp: str = '') -> bool:
    url = 'https://sctapi.ftqq.com/{0}.send'.format(sendkey)
    data = {
        'title': title,
        'desp': desp,
    }
    return post_msg(url, data)

# 函数：获取access_token
def get_access_token(token):
    access_token = ''
    try:
        url = "https://auth.aliyundrive.com/v2/account/token"
        data_dict = {
            "refresh_token": token,
            "grant_type": "refresh_token"
        }
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://www.aliyundrive.com",
            "pragma": "no-cache",
            "referer": "https://www.aliyundrive.com/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        }
        resp = requests.post(url, json=data_dict, headers=headers)
        resp_json = resp.json()
        token = {
            'access_token': resp_json.get('access_token', ""),
            'refresh_token': resp_json.get('refresh_token', ""),
            'expire_time': resp_json.get('expire_time', ""),
        }
        logger.debug(f"resp_json={resp_json}")
        access_token = token['access_token']
    except:
        logger.error(f"获取异常:{traceback.format_exc()}")
    return access_token

# 类：阿里云盘操作
class ALiYunPan(object):
    def __init__(self, access_token):
        self.access_token = access_token

    # 方法：签到
    def sign_in(self):
        sign_in_days_lists = []
        not_sign_in_days_lists = []

        try:
            token = self.access_token
            url = 'https://member.aliyundrive.com/v1/activity/sign_in_list'
            headers = {
                "Content-Type": "application/json",
                "Authorization": token,
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 D/C501C6D2-FAF6-4DA8-B65B-7B8B392901EB"
            }
            body = {}
            resp = requests.post(url, json=body, headers=headers)
            resp_text = resp.text
            resp_json = resp.json()

            code = resp_json.get('code', '')
            if code == "AccessTokenInvalid":
                logger.warning(f"请检查token是否正确")
            elif code is None:
                result = resp_json.get('result', {})
                sign_in_logs_list = result.get("signInLogs", [])
                sign_in_count = result.get("signInCount", 0)
                title = '阿里云盘签到提醒'
                msg = ''

                if len(sign_in_logs_list) > 0:
                    for i, sign_in_logs_dict in enumerate(sign_in_logs_list, 1):
                        status = sign_in_logs_dict.get('status', '')
                        day = sign_in_logs_dict.get('day', '')
                        isReward = sign_in_logs_dict.get('isReward', 'false')

                        if status == "":
                            logger.info(f"sign_in_logs_dict={sign_in_logs_dict}")
                            logger.error(f"签到信息获取异常:{resp_text}")
                        elif status == "miss":
                            not_sign_in_days_lists.append(day)
                        elif status == "normal":
                            reward = self.get_reward(day)
                            if not isReward:
                                reward = self.get_reward(day)
                            else:
                                reward = sign_in_logs_dict.get('reward', {})
                            if reward:
                                name = reward.get('name', '')
                                description = reward.get('description', '')
                            else:
                                name = '无奖励'
                                description = ''
                            today_info = '✅' if day == sign_in_count else '☑'
                            log_info = f"{today_info}打卡第{day}天，获得奖励：**[{name}->{description}]**"
                            logger.info(log_info)
                            msg = log_info + '\n\n' + msg
                            sign_in_days_lists.append(day)

                    log_info = f"🔥打卡进度:{sign_in_count}/{len(sign_in_logs_list)}"
                    logger.info(log_info)

                    msg = log_info + '\n\n' + msg
                    if PUSH_KEY:
                        ServerChan_send(PUSH_KEY, title, msg)
                    if PUSH_PLUS_TOKEN:
                        PushPlus_send(PUSH_PLUS_TOKEN, title, msg)
                else:
                    logger.warning(f"resp_json={resp_json}")
            else:
                logger.warning(f"resp_json={resp_json}")
        except:
            logger.error(f"签到异常={traceback.format_exc()}")

    # 方法：获取签到奖励
    def get_reward(self, day):
        try:
            token = self.access_token
            url = 'https://member.aliyundrive.com/v1/activity/sign_in_reward'
            headers = {
                "Content-Type": "application/json",
                "Authorization": token,
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 D/C501C6D2-FAF6-4DA8-B65B-7B8B392901EB"
            }
            body = {'signInDay': day}
            resp = requests.post(url, json=body, headers=headers)
            resp_text = resp.text
            logger.debug(f"resp_json={resp_text}")

            resp_json = resp.json()
            result = resp_json.get('result', {})
            name = result.get('name', '')
            description = result.get('description', '')
            return {'name': name, 'description': description}
        except:
            logger.error(f"获取签到奖励异常={traceback.format_exc()}")

        return {'name': 'null', 'description': 'null'}

# 主函数
def main():
    if ',' in refresh_token:
        tokens = refresh_token.split(',')
    elif '，' in refresh_token:
        tokens = refresh_token.split('，')
    else:
        tokens = [refresh_token]
    for token in tokens:
        access_token = get_access_token(token)
        if access_token:
            ali = ALiYunPan(access_token)
            ali.sign_in()

if __name__ == '__main__':
    main()
