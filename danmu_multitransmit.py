"""
向多个直播间发送弹幕，简单写个图形界面
"""
#import pandas as pd
import requests
import threading
import time
import re
import tkinter

def getCurTime():
    time_int = int(time.time())  # 简单处理，直接舍弃后面毫秒等部分
    return str(time_int)

def is_integer(s):
    try:
        int(s)
        return True
    except ValueError:
        pass
    return False

def getRoomId(simple_id):
    # 使用api获取房间的真实id
    url = "https://api.live.bilibili.com/room/v1/Room/room_init"
    data = {
        'id': simple_id
    }
    response = requests.get(url, params=data)  # 会在url后面接上"?id=xxx"
    response.raise_for_status()  # 可能请求失败

    try:
        room_id = response.json()['data']['room_id']  # 得到json格式的数据，进行字典化，根据格式获取room_id
    except TypeError:
        tkinter.messagebox.showerror(
            title='提示',
            message='请确认房间号是否正确',
        )
        raise SystemExit
    return room_id


class DanmuMultiTransimitter():
    def __init__(self, room_id_list):
        # 读一下配置
        self.msg_box_size = 16
        self.msg_list = [None] * self.msg_box_size  # 消息队列能存放msg_box_size条消息，可以动态调整
        self.msg_num = 0  # 现在队列中有几条消息待发送
        self.msg_save_index = 0  # 消息队列中的索引，存放消息时用
        self.msg_get_index = 0  # 取消息时用
        self.last_send_time = time.time()  # # 上一次弹幕发送时间，用这个来判断1s间隔可能更好一点
        self.mutex = threading.Lock()  # 一个锁，上面一些变量的访问都需要锁
        self.semaphore = threading.Semaphore(0)  # 信号量，相当于消息数，初始为0，这样run里就不用忙等待了
        # 也可以用管程来做
        """
        根据 MDN 的文档定义，请求方法为：GET、POST、HEAD，请求头 Content-Type 为：
        text/plain、multipart/form-data、application/x-www-form-urlencoded 的
        就属于 “简单请求” 不会触发 CORS 预检请求。

        如果请求头的 Content-Type 为 application/json 就会触发 CORS 预检请求，这里也会称为 “非简单请求”
        """
        self.headers = {
            'authority': 'api.live.bilibili.com',
            'accept-encoding': 'gzip, deflate, br',
            'referer': 'https://live.bilibili.com/',
        }


        self.dest_room_true_id_list = []
        for room_id in room_id_list:
            self.dest_room_true_id_list.append(getRoomId(room_id))

        try:
            # 获取cookie等信息
            with open("./config/RunningConfig.txt", 'r', encoding="utf-8") as f:
                lines = f.readlines()
                running_info = {}
                for line in lines:
                    line = line.strip(" \t\r\n")
                    if len(line) == 0:
                        continue
                    parts = re.split("[: \t\r\n]+", line, 1)
                    running_info[parts[0]] = parts[1].strip(" \r\n")

                self.csrf_token = running_info['csrf_token']
                self.cookie = running_info['cookie']
                self.send_interval = float(running_info['send_interval'])  # 发消息间隔时间，这里的间隔设置为实际需求的间隔，目前是1s

        except IOError:
            tkinter.messagebox.showerror(
                title='提示',
                message='没有找到配置文件或读入失败，exception in danmu_multitransmit.py:__init__',
            )
            print("没有找到配置文件或读入失败，exception in danmu_multitransmit.py:__init__")
            exit(-1)
        except:
            tkinter.messagebox.showerror(
                title='提示',
                message='其他错误，exception in danmu_multitransmit.py:__init__',
            )
            print("其他错误，exception in danmu_multitransmit.py:__init__")
            exit(-1)

        if len(self.csrf_token) == 0 or len(self.cookie) == 0:
            tkinter.messagebox.showerror(
                title='提示',
                message='请先设置csrf、cookie等信息',
            )
            raise SystemExit

    def sendDanmu(self, msg, room_id):
        url_to_request = "https://api.live.bilibili.com/msg/send"
        # 发送数据
        """
        :param mode: 弹幕显示模式（滚动、顶部、底部）
        :param font_size: 字体尺寸
        :param color: 颜色
        :param timestamp: 时间戳
        :param rnd: 随机数
        :param uid_crc32: 用户ID文本的CRC32
        :param msg_type: 是否礼物弹幕（节奏风暴）
        :param bubble: 右侧评论栏气泡
        :param msg: 弹幕内容
        :param uid: 用户ID
        :param uname: 用户名
        :param admin: 是否房管
        :param vip: 是否月费老爷
        :param svip: 是否年费老爷
        :param urank: 用户身份，用来判断是否正式会员，猜测非正式会员为5000，正式会员为10000
        :param mobile_verify: 是否绑定手机
        :param uname_color: 用户名颜色
        :param medal_level: 勋章等级
        :param medal_name: 勋章名
        :param runame: 勋章房间主播名
        :param room_id: 勋章房间ID
        :param mcolor: 勋章颜色
        :param special_medal: 特殊勋章
        :param user_level: 用户等级
        :param ulevel_color: 用户等级颜色
        :param ulevel_rank: 用户等级排名，>50000时为'>50000'
        :param old_title: 旧头衔
        :param title: 头衔
        :param privilege_type: 舰队类型，0非舰队，1总督，2提督，3舰长
        """
        data = {
            'color': "16777215",
            'fontsize': "25",
            'mode': "1",
            'msg': msg,
            'rnd': getCurTime(),  # 时间戳不改好像也没事
            'roomid': room_id,
            'bubble': "0",
            'csrf_token': self.csrf_token,
            'csrf': self.csrf_token
        }

        # 包含账号信息
        cookie = {'cookie': self.cookie}

        diff_time = time.time() - self.last_send_time  # 离上一次发送过了多久
        sleep_time = self.send_interval + 0.01 - diff_time  # 要等待多久才能再发，这里加0.01让时间稍微宽松一点
        # print(sleep_time)
        if sleep_time > 0:
            time.sleep(sleep_time)  # b站弹幕好像要隔1s才能发1条，所以要这样来设置

        self.last_send_time = time.time()  # 更新发送时间
        send_response = requests.post(url_to_request, headers=self.headers, data=data, cookies=cookie)
        # print(send_response.headers['date'])
        # print(send_response.elapsed.total_seconds())  # 获取响应的时间
        # 响应时间大概在0.1~0.2s左右
        send_response.raise_for_status()  # 如果出错会有相应信息
        # response = send_response.json()
        # if response['message'] == "msg in 1s":
        #    data['rnd'] = getCurTime()  # 重发
        # else:
        #    break

    def addMsg(self, msg):
        # 把消息加入到消息队列
        self.mutex.acquire()
        try:
            if self.msg_num >= self.msg_box_size:
                # 要扩容
                temp = self.msg_list
                self.msg_box_size = self.msg_box_size * 2
                self.msg_list = [None] * self.msg_box_size
                # 把原先的消息转移
                trans_index = 0
                while trans_index < self.msg_num:
                    self.msg_list[trans_index] = temp[self.msg_get_index]
                    trans_index += 1
                    self.msg_get_index = (self.msg_get_index+1) % self.msg_num  # 这里num对应原来的容量
                self.msg_get_index = 0
                self.msg_save_index = self.msg_num

            # 存下新的消息
            self.msg_num += 1
            self.msg_list[self.msg_save_index] = msg
            self.msg_save_index = (self.msg_save_index + 1) % self.msg_box_size
        finally:
            self.mutex.release()
        self.semaphore.release()  # 计数器加1

    def getMsg(self):
        # 从消息队列获取一条消息
        msg = None
        self.semaphore.acquire()  # 这个信号量可能在stop中被释放，也就是说下面msg_num可能为0，msg可能为None，对应结束情况
        self.mutex.acquire()
        try:
            if self.msg_num > 0:
                self.msg_num -= 1
                msg = self.msg_list[self.msg_get_index]
                self.msg_get_index = (self.msg_get_index+1) % self.msg_box_size
        finally:
            self.mutex.release()
        return msg

    def stop(self):
        self.semaphore.release()  # 可能之前在等的时候关闭了
        print("end!")

    def run(self):
        print("start run!")
        while True:
            msg = self.getMsg()  # 在获取消息时会等待
            if msg is not None:
                for one_id in self.dest_room_true_id_list:
                    self.sendDanmu(msg, one_id)  # send中会有相应的时间间隔
                    # print(self.msg_list)
            else:
                # 结束，得到的消息是空消息，因为stop时信号量释放了一次，但没有加入消息，所以会取到一条空消息
                break

    def start(self):
        t = threading.Thread(target=self.run)
        t.start()


if __name__ == "__main__":
    pass
