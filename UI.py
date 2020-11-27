"""
简单的图形界面
"""
from abc import ABCMeta, abstractmethod
import tkinter
import tkinter.messagebox
from tkinter import ttk
import re
import os
import datetime
import danmu_multitransmit

class DataManager():
    # 数据的读取与保存
    def __init__(self):
        self.liveRoomLibPath = './resource/data/LiveRoomLib.txt'
        self.wordFixLibPath = "./resource/data/WordFixLib.txt"

    def get_live_room_lib(self):
        try:
            # 读取保存直播间房间号的文件
            liveRoomLib = {}  # 一个字典，key为库名(不能为空，创建时限定)，value为各直播间
            with open(self.liveRoomLibPath, 'r', encoding="utf-8") as f:
                lines = f.readlines()
                lib_info = []  # 一个库的信息
                new_lib_start = False  # 要开始记录一个新的库了
                lib_name = ""
                for line in lines:
                    line = line.strip(" \t\r\n")
                    if len(line) == 0:
                        continue
                    if line == "_####":
                        # 标志一个新的库开始
                        new_lib_start = True
                        if len(lib_name) != 0:
                            # 将上一个库的信息保存
                            # 因为最后还有一行'_####'，所以最后一个库不用单独存
                            liveRoomLib[lib_name] = lib_info
                            lib_info = []
                            lib_name = ""
                        continue
                    if new_lib_start:
                        # 先得到库名
                        lib_name = line
                        new_lib_start = False
                        continue
                    # 其他时候就存一下各直播间信息
                    parts = re.split(",", line, 1)  # 逗号分割
                    lib_info.append((parts[0], parts[1]))  # (名字,房间号)
        except IOError:
            print("没有找到直播间库文件或读入失败，exception in MainInterface:__init__")
            exit(-1)
        except:
            print("读取直播间库时出错，exception in ManagerInterface:__init__")
            exit(-1)

        return liveRoomLib

    def get_word_fix_lib(self):
        try:
            # 读取前后缀库
            wordFixLib = {}  # 一个字典，key为前后缀名(不能为空，创建时限定)，value为具体前后缀
            with open(self.wordFixLibPath, 'r', encoding="utf-8") as f:
                all_lines = f.readlines()
                lib_info = []  # 一个库的信息
                new_lib_start = False  # 要开始记录一个新的库了
                lib_name = ""
                content_sample = ""  # 示例，即前后缀分割符

                for line in all_lines:
                    line = line.strip("\r\n")  # 空格也可以
                    if len(line) == 0:
                        continue
                    if line == "_####":
                        # 标志一个新的库开始
                        new_lib_start = True
                        if len(lib_name) != 0:
                            # 将上一个库的信息保存
                            # 因为最后还有一行'_####'，所以最后一个库不用单独存
                            lib_info.insert(0, content_sample)  # 其他各项都是二元组(前缀，后缀)
                            # 第一项特殊，保存分割符，放到最前面
                            wordFixLib[lib_name] = lib_info
                            lib_info = []
                            lib_name = ""
                            content_sample = ""
                        continue
                    if new_lib_start:
                        # 先得到库名和示例(前后缀分割符)
                        parts = re.split(",", line, 1)  # 逗号分割
                        lib_name = parts[0]
                        content_sample = parts[1]
                        new_lib_start = False
                        continue
                    # 其他时候就存一下各前后缀信息
                    fix_parts = re.split(content_sample, line, 1)
                    lib_info.append((fix_parts[0], fix_parts[1]))  # (前缀,后缀)
        except IOError:
            print("没有找到前后缀库文件或读入失败，exception in MainInterface:__init__")
            exit(-1)
        except:
            print("读取前后缀库时出错，exception in MainInterface:__init__")
            exit(-1)

        return wordFixLib

    def save_live_room_lib(self, live_room_lib):
        try:
            with open(self.liveRoomLibPath, 'w', encoding="utf-8") as f:
                for lib_name in live_room_lib.keys():
                    f.write('_####\n')  # 第一行
                    f.write(lib_name+'\n')  # 第二行
                    room_list = live_room_lib[lib_name]
                    for room in room_list:
                        f.write(room[0]+','+room[1]+'\n')
                f.write('_####\n')  # 最后一行
        except IOError:
            print("没有找到直播间库文件或读入失败，exception in DataManager:save_live_room_lib")
            exit(-1)
        except:
            print("读取直播间库时出错，exception in DataManager:save_live_room_lib")
            exit(-1)

    def save_word_fix_lib(self, word_fix_lib):
        try:
            with open(self.wordFixLibPath, 'w', encoding="utf-8") as f:
                for lib_name in word_fix_lib.keys():
                    f.write('_####\n')  # 第一行
                    word_fix_list = word_fix_lib[lib_name]
                    content_sample = word_fix_list[0]
                    f.write(lib_name + ',' + content_sample + '\n')  # 第二行
                    # word_fix_list.remove(content_sample)
                    # 不能删除，会改变数据
                    for i in range(1, len(word_fix_list)):
                        word_fix = word_fix_list[i]
                        f.write(word_fix[0] + content_sample + word_fix[1] + '\n')
                f.write('_####\n')  # 最后一行
        except IOError:
            print("没有找到直播间库文件或读入失败，exception in DataManager:save_word_fix_lib")
            exit(-1)
        except:
            print("读取直播间库时出错，exception in DataManager:save_word_fix_lib")
            exit(-1)


class BaseFrame(tkinter.Frame):
    __metaclass__ = ABCMeta

    def __init__(self, master, height=None, width=None):
        tkinter.Frame.__init__(
            self,
            master,
            height=height,
            width=width
        )

    @abstractmethod
    def create_widgets(self):
        raise NotImplementedError


class MainInterface():
    def __init__(self, setting_manager,  room_id_list, content_sample, word_fix_list):
        self.setting_manager = setting_manager  # 设置界面
        self.transmitter = None  # 发送线程，在run中创建，stop中关闭
        self.root = tkinter.Tk()
        self.root.title('向多个直播间发送弹幕')
        self.root.minsize(200, 180)
        width = 480
        height = 180
        to_left = (self.root.winfo_screenwidth() - width) / 2
        to_top = (self.root.winfo_screenheight() - height) / 2
        # 居中
        self.root.geometry("%dx%d+%d+%d" % (width, height, to_left, to_top))
        self.root.configure(background='gray')

        self.room_id_list = room_id_list
        self.content_sample = content_sample
        self.word_fix = word_fix_list
        self.word_fix_index = 0  # 索引，用于切换前后缀

        try:
            if not os.path.exists("./history/"):
                # 保存历史记录
                os.makedirs("./history/")  # 创建文件夹
        except:
            tkinter.messagebox.showerror(
                title='提示',
                message='创建history文件夹失败，exception in MainInterface:__init__',
                parent=self.root  # 这样才会显示在当前窗口上方
            )
            print("创建history文件夹失败，exception in MainInterface:__init__")
            exit(-1)
        cur_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d_%H-%M-%S')
        # 创建文件用来存数据，文件名不能有'< > / \ | : " * ?'这些字符
        try:
            self.Logger = open("./history/"+cur_time+".txt", "a", encoding="utf-8")
            self.Logger.write('room_list:'+ str(room_id_list) + '\n')
            self.Logger.write('content_sample:' + content_sample + '\n')
            self.Logger.write('word_fix_list:' + str(word_fix_list) + '\n')
            self.Logger.write('####\n')
        except IOError:
            tkinter.messagebox.showerror(
                title='提示',
                message='日志文件创建或写入失败，exception in MainInterface:__init__',
                parent=self.root  # 这样才会显示在当前窗口上方
            )
            print("日志文件创建或写入失败，exception in MainInterface:__init__")
            exit(-1)
        try:
            with open("./config/UIConfig.txt", 'r', encoding="utf-8") as f:
                data_dict = {}
                all_lines = f.readlines()
                for line in all_lines:
                    line = line.strip(" \r\n")
                    if len(line) == 0:
                        continue
                    parts = re.split("[: \t\r\n]+", line, 1)  # 可能字体名自带空格所以分割数设置1
                    data_dict[parts[0]] = parts[1]  # 存到字典

                # 获取字体名
                the_font = data_dict['font']
                the_font = the_font.strip(" \r\n")  # 去首尾空白符
                self.font = re.split(",", the_font)  # 有字体和字体大小
        except IOError:
            tkinter.messagebox.showerror(
                title='提示',
                message='没有找到UI配置文件或读入失败，exception in MainInterface:__init__',
                parent=self.root  # 这样才会显示在当前窗口上方
            )
            print("没有找到UI配置文件或读入失败，exception in MainInterface:__init__")
            exit(-1)
        except:
            tkinter.messagebox.showerror(
                title='提示',
                message='其他错误，exception in MainInterface:__init__',
                parent=self.root  # 这样才会显示在当前窗口上方
            )
            print("其他错误，exception in MainInterface:__init__")
            exit(-1)

        self.word_count_label = tkinter.Label(
            self.root,
            text=str(self.getFixLen()) + '/30',  # 已经有前后缀了
            bg='gray',
            font=(self.font[0], 10),
            width=10,
            height=2
        )
        self.word_count_label.place(relx=0, rely=0, width=70, height=20)

        initial_sample_text = "xx"
        if len(self.word_fix) > 0:
            initial_sample_text = self.word_fix[0][0]+self.content_sample+self.word_fix[0][1]
        self.word_sample_label = tkinter.Label(
            self.root,
            text=initial_sample_text,
            bg='gray',
            font=(self.font[0], 10),
            width=10,
            height=2
        )
        self.word_sample_label.place(relx=0, y=20, width=70, height=20)

        """
        registry_validate_command = \
            self.root.register(self.entryNumValidate)  # 一定要这里先注册下面的validatecommand才可以带参
        self.text_input = tkinter.Entry(
            self.root,
            # textvariable=self.word_count,  # 反馈字数变化
            validate='key',  # 值变化时进行验证，要限制字数
            validatecommand=(registry_validate_command, '%P'),  # 验证函数，要返回True或False，表示是否验证成功
            fg='white',
            bg='#2B2B2B',
            font=(self.font[0], int(self.font[1]))
        )
        """
        # 这里改一下不再进行字数限制，超过字数自动分段
        # 除了要改这里的验证函数，还要改前后缀切换那里，之前是更改前后缀后超过30要裁剪，现在不用了
        registry_validate_command = \
            self.root.register(self.entryChange)  # 一定要这里先注册下面的validatecommand才可以带参
        self.text_input = tkinter.Entry(
            self.root,
            validate='key',  # 值变化时进行跟踪
            validatecommand=(registry_validate_command, '%P'),  # 验证函数，要返回True或False，表示是否验证成功
            fg='white',
            bg='#2B2B2B',
            font=(self.font[0], int(self.font[1]))
        )
        self.text_input.place(x=75, y=10, relwidth=0.64)
        self.text_input.configure(insertbackground='white')

        # 设置一个返回按钮
        self.buttonstyle = tkinter.ttk.Style()
        self.buttonstyle.configure(  # 定义一个style，后面能用
            'own.TButton'
            # background='#808080'
        )
        # 简单设置一个theme
        self.buttonstyle.theme_use('xpnative')
        self.back_button = ttk.Button(  # 注意是ttk的button
            self.root,
            text='返回',
            style='own.TButton',
            command=self.backToSetting
        )
        self.back_button.place(relx=0.8, y=6, height=24, width=100)

        self.text_history = tkinter.Text(
            self.root,
            font=(self.font[0], int(self.font[1])),
            bg='#2B2B2B',
            fg='white'
        )
        self.text_history.place(relx=0, y=40, relwidth=1, relheight=0.88)
        self.text_history.config(state=tkinter.DISABLED)  # 禁止输入，自己要输入时再改normal

        self.root.protocol("WM_DELETE_WINDOW", self.stop)  # 重写关闭窗口时的处理

        self.root.unbind("<Tab>")
        self.root.unbind("<Alt_L>")
        self.text_input.unbind("<Tab>")
        self.text_input.unbind("<Alt_L>")
        self.text_history.unbind("<Tab>")
        self.text_history.unbind("<Alt_L>")

        self.text_input.bind("<Return>", self.submitInputContent)  # 按下回车提交输入
        self.text_input.bind("<Up>", self.changeWordFixBackward)  # 上下方向键改变前后缀
        self.text_input.bind("<Down>", self.changeWordFixForward)  # 上下方向键改变前后缀
        self.root.bind("<Tab>", self.changeWordFixForward)  # tab键改变前后缀
        self.root.bind("<Alt_L>", self.changeWordFixBackward)  # alt键改变前后缀

    def entryChange(self, new_str):
        # 是对下面字数限制函数的修改，不再限制字数
        # 加这个函数只是为了追踪每次输入变化，别的绑定方法应该也可以，这里简单处理，沿用之前的
        total_len = len(new_str) + self.getFixLen()
        self.word_count_label['text'] = str(total_len) + "/30"  # 更改字数显示
        return True  # 不管输入多长都是返回True

    def entryNumValidate(self, new_str):
        # 输入字数验证
        # print(len(new_str))
        total_len = len(new_str) + self.getFixLen()
        if total_len <= 30:  # 加上前后缀后不超过限定
            self.word_count_label['text'] = str(total_len) + "/30"  # 更改字数显示
            return True
        return False

    def submitInputContent(self, event):
        # 提交一行输入
        # 修改过后字数超出限制自动分行
        content = self.text_input.get()
        limit_len = 30-self.getFixLen()  # 一次能填多长内容
        if content is not None:
            while len(content) != 0:
                to_send = content
                if len(to_send) > limit_len:
                    # 要分段
                    to_send = content[0:limit_len]
                    content = content[limit_len:len(content)]
                else:
                    content = ''  # 长度置0

                if len(self.word_fix) > 0:
                    the_fix = self.word_fix[self.word_fix_index]
                    self.Logger.write(the_fix[0] + the_fix[1] + ":" + to_send + "\n")  # 记录
                    to_send = the_fix[0] + to_send + the_fix[1]  # 加上前后缀
                else:
                    self.Logger.write(":" + to_send + "\n")  # 记录

                self.text_history.config(state=tkinter.NORMAL)  # 之后再改为禁止
                self.text_history.insert(tkinter.END, to_send+"\n")
                self.text_history.see(tkinter.END)  # 显示最后部分
                self.text_input.delete(0, tkinter.END)

                self.text_history.config(state=tkinter.DISABLED)  # 禁止输入，自己要输入时再改normal

                self.transmitter.addMsg(to_send)

    def getFixLen(self):
        if len(self.word_fix) == 0:
            return 0
        fix_len = len(self.word_fix[self.word_fix_index][0]) + \
                  len(self.word_fix[self.word_fix_index][1])  # 前后缀加起来有多长
        return fix_len

    def changeWordFixForward(self, event):
        # 改变前后缀，向后找
        if len(self.word_fix) == 0:
            return 'break'  # 阻止事件继续传递
        new_index = (self.word_fix_index+1) % len(self.word_fix)
        if new_index < len(self.word_fix):
            self.word_fix_index = new_index
            self.word_sample_label['text'] = self.word_fix[self.word_fix_index][0] + \
                                             self.content_sample + \
                                             self.word_fix[self.word_fix_index][1]

            fix_len = self.getFixLen()
            # 现在不用裁剪了
            """
            left_len = 30 - fix_len  # 剩余可用长度
            if len(self.text_input.get()) > left_len:
                # 裁剪
                self.text_input.delete(left_len ,tkinter.END)
            """
            self.word_count_label['text'] = str(fix_len+len(self.text_input.get())) + "/30"  # 更改字数显示
        return 'break'  # 阻止事件继续传递

    def changeWordFixBackward(self, event):
        # 改变前后缀，向前找
        new_index = self.word_fix_index - 1
        if new_index < 0:
                new_index += len(self.word_fix)

        if new_index >= 0:  # 如果word_fix长度为零就直接返回，不过应该不会有这样的情况
            self.word_fix_index = new_index
            self.word_sample_label['text'] = self.word_fix[self.word_fix_index][0] + \
                                             self.content_sample + \
                                             self.word_fix[self.word_fix_index][1]

            fix_len = self.getFixLen()
            # 现在不用裁剪了
            """
            left_len = 30 - fix_len  # 剩余可用长度
            if len(self.text_input.get()) > left_len:
                # 裁剪
                self.text_input.delete(left_len, tkinter.END)
            """
            self.word_count_label['text'] = str(fix_len + len(self.text_input.get())) + "/30"  # 更改字数显示

        return 'break'  # 阻止事件继续传递

    def backToSetting(self):
        # 关闭当前界面，主要是为了重建transmitter
        if self.transmitter is not None:
            self.transmitter.stop()  # 关闭线程
        self.transmitter = None
        self.Logger.flush()  # 写出并关闭记录文件
        self.Logger.close()
        self.root.destroy()
        # 返回设置界面
        self.setting_manager.restart_setting_page()

    def stop(self):
        if self.transmitter is not None:
            self.transmitter.stop()  # 关闭线程
        self.transmitter = None
        self.Logger.flush()  # 写出并关闭记录文件
        self.Logger.close()
        self.root.destroy()
        if self.setting_manager is not None:
            self.setting_manager.stop()  # 因为正常情况下这个窗口只是隐藏，为了能再返回，最后退出时要关闭

    def run(self):
        self.transmitter = danmu_multitransmit.DanmuMultiTransimitter(self.room_id_list)
        self.transmitter.start()
        self.root.mainloop()


class LiverRoomSettingFrame(BaseFrame):
    def __init__(self, parent, controller, live_room_lib):
        parent.update()  # update之后才可以获取到最新的宽度和高度
        BaseFrame.__init__(
            self,
            parent,
            height=parent.winfo_height(),
            width=parent.winfo_width()
        )
        self.parent = parent
        self.controller = controller
        self.live_room_lib = live_room_lib  # 一个字典，库名为key，房间列表为value
        self.sending_list = []  # 用一个列表保存，列表元素(名称,房间号)
        self.create_widgets()

    def create_widgets(self):
        # 从上往下设计
        self.lib_select_group = tkinter.LabelFrame(
            self,
            text='已存直播间库目录'
        )
        self.lib_select_group.place(x=10, y=10, height=60, width=780)

        self.combostyle = tkinter.ttk.Style()
        self.combostyle.configure(  # 定义一个style，后面能用
            'own.TCombobox'
        )
        # 不是很会设置Combobox，网上教程都不太全，这里简单设置一个theme
        self.combostyle.theme_use('xpnative')
        # print(combostyle.element_names())
        # print(combostyle.element_options('Combobox.rightdownarrow'))

        self.room_lib_tracer = tkinter.StringVar()
        self.room_lib_tracer.trace("w", self.on_lib_selected)  # 值被修改时调用函数
        self.lib_select_combo = ttk.Combobox(
            self.lib_select_group,
            takefocus=0,  # 取消焦点
            state='readonly',
            style='own.TCombobox',
            values=list(self.live_room_lib.keys()),
            textvariable=self.room_lib_tracer
        )
        self.lib_select_combo.place(x=10, y=5, height=24, width=540)
        # 下拉框选择之后，调用相应函数
        # 还是用StringVar好，这样初始化的时候的设置也能捕捉到
        # self.lib_select_combo.bind("<<ComboboxSelected>>", self.on_lib_selected)

        self.buttonstyle = tkinter.ttk.Style()
        self.buttonstyle.configure(  # 定义一个style，后面能用
            'own.TButton'
        )
        # 简单设置一个theme
        self.buttonstyle.theme_use('xpnative')
        self.create_lib_button = ttk.Button(  # 注意是ttk的button
            self.lib_select_group,
            text='新建',
            style='own.TButton',
            command=self.on_lib_create
        )
        self.create_lib_button.place(x=560, y=3, height=28, width=100)

        self.delete_lib_button = ttk.Button(  # 注意是ttk的button
            self.lib_select_group,
            text='删除',
            style='own.TButton',
            command=self.on_lib_delete
        )
        self.delete_lib_button.place(x=670, y=3, height=28, width=100)
        if len(self.lib_select_combo['values']) == 0:
            self.delete_lib_button.configure(state=tkinter.DISABLED)

        ##########################################
        # 下面是显示库中内容了
        self.lib_show_group = tkinter.LabelFrame(
            self,
            text='直播间库'
        )
        self.lib_show_group.place(x=10, y=70, height=360, width=335)

        self.lib_show_content = tkinter.Listbox(
            self.lib_show_group,
            activestyle='none',  # 默认是有下划线的
            bd=1,
            highlightthickness=0,
            # relief='flat'  # 用默认sunken
        )
        self.lib_show_content.place(x=10, y=10, height=260, width=315)
        self.lib_show_content.bind('<<ListboxSelect>>', self.on_lib_room_selected)

        self.add_room_to_cur_list_button = ttk.Button(  # 注意是ttk的button
            self.lib_show_group,
            text='添加房间至本次发送列表->',
            style='own.TButton',
            command=self.on_add_room_to_cur_list
        )
        self.add_room_to_cur_list_button.place(x=10, y=272, height=28, width=315)

        self.create_room_in_lib = ttk.Button(  # 注意是ttk的button
            self.lib_show_group,
            text='新建',
            style='own.TButton',
            command=self.on_create_room_in_lib
        )
        self.create_room_in_lib.place(x=10, y=305, height=28, width=100)

        self.modify_room_in_lib = ttk.Button(  # 注意是ttk的button
            self.lib_show_group,
            text='修改',
            style='own.TButton',
            command=self.on_modify_room_in_lib
        )
        self.modify_room_in_lib.place(x=115, y=305, height=28, width=105)

        self.delete_room_in_lib = ttk.Button(  # 注意是ttk的button
            self.lib_show_group,
            text='删除',
            style='own.TButton',
            command=self.on_delete_room_in_lib
        )
        self.delete_room_in_lib.place(x=225, y=305, height=28, width=100)

        self.add_room_to_cur_list_button.configure(state=tkinter.DISABLED)  # 选择一个直播间后才能进行添加
        self.create_room_in_lib.configure(state=tkinter.DISABLED)  # 可能遇到没有库的情况
        self.modify_room_in_lib.configure(state=tkinter.DISABLED)  # 也要先选中
        self.delete_room_in_lib.configure(state=tkinter.DISABLED)  # 也要先选中

        # 这个初始化选择要放在创建lib_show_content之后
        # 因为StringVar绑定了函数，函数里要用到lib_show_content
        if len(self.live_room_lib) > 0:
            # 选中第一个库
            self.lib_select_combo.current(0)

        ##################################################
        # 下面是当前已添加的直播间
        self.sending_group = tkinter.LabelFrame(
            self,
            text='本次发送的直播间(先后顺序对应发送顺序)'
        )
        self.sending_group.place(x=375, y=70, height=360, width=380)

        self.sending_list_show_content = tkinter.Listbox(
            self.sending_group,
            activestyle='none',  # 默认是有下划线的
            bd=1,
            highlightthickness=0,
            # relief='flat'  # 用默认sunken
        )
        self.sending_list_show_content.place(x=10, y=10, height=260, width=315)
        self.sending_list_show_content.bind('<<ListboxSelect>>', self.on_sending_room_selected)

        self.copy_room_to_lib_button = ttk.Button(  # 注意是ttk的button
            self.sending_group,
            text='<-复制房间至库中',
            style='own.TButton',
            command=self.on_copy_room_to_lib
        )
        self.copy_room_to_lib_button.place(x=10, y=272, height=28, width=315)

        self.create_room_in_sending_list = ttk.Button(  # 注意是ttk的button
            self.sending_group,
            text='新建',
            style='own.TButton',
            command=self.on_create_room_in_sending_list
        )
        self.create_room_in_sending_list.place(x=10, y=305, height=28, width=100)

        self.modify_room_in_sending_list = ttk.Button(  # 注意是ttk的button
            self.sending_group,
            text='修改',
            style='own.TButton',
            command=self.on_modify_room_in_sending_list
        )
        self.modify_room_in_sending_list.place(x=115, y=305, height=28, width=105)

        self.delete_room_in_sending_list = ttk.Button(  # 注意是ttk的button
            self.sending_group,
            text='删除',
            style='own.TButton',
            command=self.on_delete_room_in_sending_list
        )
        self.delete_room_in_sending_list.place(x=225, y=305, height=28, width=100)

        self.copy_room_to_lib_button.configure(state=tkinter.DISABLED)  # 选择一个直播间后才能进行复制
        self.modify_room_in_sending_list.configure(state=tkinter.DISABLED)  # 也要先选中
        self.delete_room_in_sending_list.configure(state=tkinter.DISABLED)  # 也要先选中

        # 还有一排小"按钮"

        self.up_img = tkinter.PhotoImage(
            file='./resource/figure/up.png'
        )
        self.up_button = tkinter.Button(
            self.sending_group,
            image=self.up_img,
            command=self.move_up_in_sending_list
        )
        self.up_button.place(x=332, y=70, height=36, width=36)

        self.down_img = tkinter.PhotoImage(
            file='./resource/figure/down.png'
        )
        self.down_button = tkinter.Button(
            self.sending_group,
            image=self.down_img,
            command=self.move_down_in_sending_list
        )
        self.down_button.place(x=332, y=110, height=36, width=36)

        self.up_to_top_img = tkinter.PhotoImage(
            file='./resource/figure/up_to_top.png'
        )
        self.up_to_top_button = tkinter.Button(
            self.sending_group,
            image=self.up_to_top_img,
            command=self.up_to_top_in_sending_list
        )
        self.up_to_top_button.place(x=332, y=150, height=36, width=36)

        self.down_to_buttom_img = tkinter.PhotoImage(
            file='./resource/figure/down_to_buttom.png'
        )
        self.down_to_bottom_button = tkinter.Button(
            self.sending_group,
            image=self.down_to_buttom_img,
            command=self.down_to_bottom_in_sending_list
        )
        self.down_to_bottom_button.place(x=332, y=190, height=36, width=36)

        self.up_button.configure(state=tkinter.DISABLED)
        self.down_button.configure(state=tkinter.DISABLED)
        self.up_to_top_button.configure(state=tkinter.DISABLED)
        self.down_to_bottom_button.configure(state=tkinter.DISABLED)

        ##############################################
        # 最后再加一个按钮，到下一页设定
        self.goto_next_page_button = ttk.Button(  # 注意是ttk的button
            self,
            text='下一页',
            style='own.TButton',
            command=self.goto_next_page
        )
        self.goto_next_page_button.place(x=680, y=440, height=28, width=110)

    def get_live_room_lib(self):
        return self.live_room_lib

    def get_sending_list(self):
        return self.sending_list

    def goto_next_page(self):
        self.controller.goto_next_page()

    def on_lib_selected(self, *args):
        # 获取库的名字，也就是库字典的key，以此得到房间列表
        if len(self.lib_select_combo['values']) == 0:  # 没有元素可以选了
            self.lib_show_content.delete(0, tkinter.END)
            self.create_room_in_lib.configure(state=tkinter.DISABLED)  # 没有库不能新建
            self.lib_show_content.configure(state=tkinter.DISABLED)
            self.add_room_to_cur_list_button.configure(state=tkinter.DISABLED)
            self.modify_room_in_lib.configure(state=tkinter.DISABLED)
            self.delete_room_in_lib.configure(state=tkinter.DISABLED)
            return
        self.create_room_in_lib.configure(state=tkinter.NORMAL)
        self.lib_show_content.configure(state=tkinter.NORMAL)
        room_list = self.live_room_lib[self.lib_select_combo.get()]
        # 然后根据这个更新listbox
        self.lib_show_content.delete(0, tkinter.END)
        for one_room in room_list:
            self.lib_show_content.insert(tkinter.END, one_room[0])
        # print(room_list)
        # print(self.lib_show_content.curselection())
        # 重选库之后原先的选择信息清空，一些按钮失效
        self.add_room_to_cur_list_button.configure(state=tkinter.DISABLED)
        self.modify_room_in_lib.configure(state=tkinter.DISABLED)
        self.delete_room_in_lib.configure(state=tkinter.DISABLED)

    def on_lib_create(self, *args):
        # 创建一个库，弹出一个界面
        new_window = tkinter.Toplevel()
        new_window.title("创建库")
        new_window.attributes('-topmost', True)
        width = 320
        height = 100
        to_left = (new_window.winfo_screenwidth() - width) / 2
        to_top = (new_window.winfo_screenheight() - height) / 2
        # 居中
        new_window.geometry("%dx%d+%d+%d" % (width, height, to_left, to_top))
        new_window.grab_set()  # 这一句使得新窗口捕获所有事件
        new_window.focus_force()  # 获取焦点

        tip_label = tkinter.Label(
            new_window,
            text='库名称:'
        )
        tip_label.place(x=10, y=10, height=20, width=40)
        lib_name_entry = tkinter.Entry(
            new_window
        )
        lib_name_entry.place(x=10, y=40, height=25, width=300)
        lib_name_entry.focus_force()

        def on_confirm_clicked(*args):
            name = lib_name_entry.get().strip(' \t\r\n')  # 去除首尾空白符
            if len(name) == 0:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='名称不能只由空白符构成',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
            elif name in self.lib_select_combo['values']:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='库名已存在',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
            elif name == '_####':
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='库名不能为\'_####\'',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
            else:
                # insert好像没用
                self.live_room_lib[name] = []  # 新建的库为空
                self.lib_select_combo['values'] = tuple(self.lib_select_combo['values']) + (name,)
                self.lib_select_combo.current(len(self.lib_select_combo['values']) - 1)  # 显示最新的
                self.delete_lib_button.configure(state=tkinter.NORMAL)
                new_window.destroy()  # 关闭窗口

        confirm_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='确认',
            style='own.TButton',
            command=on_confirm_clicked
        )
        confirm_button.place(x=140, y=70, height=25, width=80)
        cancel_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='取消',
            style='own.TButton',
            command=new_window.destroy  # 按钮按下，关闭窗口
        )
        cancel_button.place(x=230, y=70, height=25, width=80)

    def on_lib_delete(self, *args):
        # 删除一个库
        # 这里直接用delete好像删不掉
        all_libs = self.lib_select_combo['values']
        delete_index = all_libs.index(self.lib_select_combo.get())  # 元组里如果没找到该元素会抛出异常，但这里肯定能找到
        self.lib_select_combo['values'] = all_libs[:delete_index] + all_libs[delete_index + 1:]
        del self.live_room_lib[self.lib_select_combo.get()]  # 字典的删除
        if len(self.lib_select_combo['values']) > 0:
            # 选中第一项
            self.lib_select_combo.current(0)
        else:
            self.lib_select_combo.set("")
            self.delete_lib_button.configure(state=tkinter.DISABLED)

        # sending_list也更新一下，为了重选，不然一些按钮信息不同步
        room_list = self.sending_list
        # 更新listbox
        self.sending_list_show_content.delete(0, tkinter.END)
        for one_room in room_list:
            self.sending_list_show_content.insert(tkinter.END, one_room[0])

        self.copy_room_to_lib_button.configure(state=tkinter.DISABLED)
        self.modify_room_in_sending_list.configure(state=tkinter.DISABLED)
        self.delete_room_in_sending_list.configure(state=tkinter.DISABLED)

        self.up_button.configure(state=tkinter.DISABLED)
        self.up_to_top_button.configure(state=tkinter.DISABLED)
        self.down_button.configure(state=tkinter.DISABLED)
        self.down_to_bottom_button.configure(state=tkinter.DISABLED)

    def on_lib_room_selected(self, event):
        # 当库中的一个房间被选中时
        if len(self.lib_show_content.curselection()) > 0:
            # 因为这个事件在listbox被改变时也能触发，不一定是选中，所以加一个判断
            self.add_room_to_cur_list_button.configure(state=tkinter.NORMAL)
            self.modify_room_in_lib.configure(state=tkinter.NORMAL)
            self.delete_room_in_lib.configure(state=tkinter.NORMAL)
        else:
            self.add_room_to_cur_list_button.configure(state=tkinter.DISABLED)
            self.modify_room_in_lib.configure(state=tkinter.DISABLED)
            self.delete_room_in_lib.configure(state=tkinter.DISABLED)

    def on_add_room_to_cur_list(self, *args):
        # 为本次发送弹幕添加一个直播间
        room_name = self.lib_show_content.selection_get()  # 当前选中房间的名称
        room_list = self.live_room_lib[self.lib_select_combo.get()]
        cur_index = 0  # 当前选中房间的索引
        for i in range(len(room_list)):
            if room_name == room_list[i][0]:
                cur_index = i
                break
        for sending_room in self.sending_list:
            if room_name == sending_room[0]:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='名称已存在',
                    parent=self  # 这样才会显示在当前窗口上方
                )
                return
        self.sending_list.append(room_list[cur_index])
        # 更新listbox
        self.sending_list_show_content.delete(0, tkinter.END)
        for one_room in self.sending_list:
            self.sending_list_show_content.insert(tkinter.END, one_room[0])
        # 一些按钮失效
        self.copy_room_to_lib_button.configure(state=tkinter.DISABLED)
        self.modify_room_in_sending_list.configure(state=tkinter.DISABLED)
        self.delete_room_in_sending_list.configure(state=tkinter.DISABLED)

    def on_create_room_in_lib(self, *args):
        # 新建一个房间信息，添加到当前库中
        # 弹出一个界面
        new_window = tkinter.Toplevel()
        new_window.title("添加新房间")
        new_window.attributes('-topmost', True)
        width = 320
        height = 100
        to_left = (new_window.winfo_screenwidth() - width) / 2
        to_top = (new_window.winfo_screenheight() - height) / 2
        # 居中
        new_window.geometry("%dx%d+%d+%d" % (width, height, to_left, to_top))
        new_window.grab_set()  # 这一句使得新窗口捕获所有事件
        new_window.focus_force()  # 获取焦点

        name_label = tkinter.Label(
            new_window,
            text='名称:'
        )
        name_label.place(x=10, y=10, height=20, width=40)
        name_entry = tkinter.Entry(
            new_window
        )
        name_entry.place(x=55, y=10, height=25, width=246)
        name_entry.focus_force()

        # 房间号只能是数字
        def isIntegerValidate(new_str):
            if ' ' in new_str:
                return False
            if len(new_str) == 0:
                return True
            try:
                int(new_str)
                return True
            except ValueError:
                pass
            return False

        registry_validate_command = \
            self.register(isIntegerValidate)  # 一定要这里先注册下面的validatecommand才可以带参
        room_id_label = tkinter.Label(
            new_window,
            text='房间号:'
        )
        room_id_label.place(x=10, y=40, height=20, width=40)
        room_id_entry = tkinter.Entry(
            new_window,
            validate='key',  # 值变化时进行验证
            validatecommand=(registry_validate_command, '%P'),  # 验证函数，要返回True或False，表示是否验证成功
        )
        room_id_entry.place(x=55, y=40, height=25, width=246)

        def on_confirm_clicked(*args):
            name = name_entry.get().strip(' \t\r\n')  # 去除首尾空白符
            room_id = room_id_entry.get().strip('\r\n')
            if len(name) == 0 or len(room_id) == 0:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='名称、房间号不能为空',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
                return
            # 能按下这个按钮肯定是有库的
            already_has = False
            room_list = self.live_room_lib[self.lib_select_combo.get()]
            for one_pair in room_list:
                if name == one_pair[0]:
                    already_has = True
                    break
            if already_has:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='名称已存在',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
            else:
                # insert好像没用
                self.live_room_lib[self.lib_select_combo.get()].append((name, room_id))
                self.lib_select_combo.current(self.lib_select_combo.current())  # 不带参的current返回当前索引
                # 这里是要再选一遍，来更新show_content中的内容
                new_window.destroy()  # 关闭窗口

        confirm_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='确认',
            style='own.TButton',
            command=on_confirm_clicked
        )
        confirm_button.place(x=140, y=70, height=25, width=80)
        cancel_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='取消',
            style='own.TButton',
            command=new_window.destroy  # 按钮按下，关闭窗口
        )
        cancel_button.place(x=230, y=70, height=25, width=80)

    def on_modify_room_in_lib(self, *args):
        # 修改库中一个房间的信息
        room_name = self.lib_show_content.selection_get()  # 当前选中房间的名称
        room_list = self.live_room_lib[self.lib_select_combo.get()]
        cur_index = 0  # 当前选中房间的索引
        for i in range(len(room_list)):
            if room_name == room_list[i][0]:
                cur_index = i
                break
        # 接下来和创建界面类似，只不过有初始值
        # 弹出一个界面
        new_window = tkinter.Toplevel()
        new_window.title("修改房间信息")
        new_window.attributes('-topmost', True)
        width = 320
        height = 100
        to_left = (new_window.winfo_screenwidth() - width) / 2
        to_top = (new_window.winfo_screenheight() - height) / 2
        # 居中
        new_window.geometry("%dx%d+%d+%d" % (width, height, to_left, to_top))
        new_window.grab_set()  # 这一句使得新窗口捕获所有事件
        new_window.focus_force()  # 获取焦点

        name_label = tkinter.Label(
            new_window,
            text='名称:'
        )
        name_label.place(x=10, y=10, height=20, width=40)
        name_entry = tkinter.Entry(
            new_window
        )
        name_entry.insert(0, room_list[cur_index][0])  # 设置初始值
        name_entry.place(x=55, y=10, height=25, width=246)
        name_entry.focus_force()

        # 房间号只能是数字
        def isIntegerValidate(new_str):
            if ' ' in new_str:
                return False
            if len(new_str) == 0:
                return True
            try:
                int(new_str)
                return True
            except ValueError:
                pass
            return False

        registry_validate_command = \
            self.register(isIntegerValidate)  # 一定要这里先注册下面的validatecommand才可以带参
        room_id_label = tkinter.Label(
            new_window,
            text='房间号:'
        )
        room_id_label.place(x=10, y=40, height=20, width=40)
        room_id_entry = tkinter.Entry(
            new_window,
            validate='key',  # 值变化时进行验证
            validatecommand=(registry_validate_command, '%P'),  # 验证函数，要返回True或False，表示是否验证成功
        )
        room_id_entry.insert(0, room_list[cur_index][1])  # 设置初始值
        room_id_entry.place(x=55, y=40, height=25, width=246)

        def on_confirm_clicked(*args):
            name = name_entry.get().strip(' \t\r\n')  # 去除首尾空白符
            room_id = room_id_entry.get().strip('\r\n')
            if len(name) == 0 or len(room_id) == 0:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='名称、房间号不能为空',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
                return
            # 能按下这个按钮肯定是有库的
            already_has = False
            for i in range(len(room_list)):
                if i != cur_index:
                    if name == room_list[i][0]:
                        already_has = True
                        break
            if already_has:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='名称已存在',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
            else:
                # insert好像没用
                self.live_room_lib[self.lib_select_combo.get()][cur_index] = (name, room_id)
                self.lib_select_combo.current(self.lib_select_combo.current())  # 不带参的current返回当前索引
                # 这里是要再选一遍，来更新show_content中的内容
                new_window.destroy()  # 关闭窗口

        confirm_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='确认',
            style='own.TButton',
            command=on_confirm_clicked
        )
        confirm_button.place(x=140, y=70, height=25, width=80)
        cancel_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='取消',
            style='own.TButton',
            command=new_window.destroy  # 按钮按下，关闭窗口
        )
        cancel_button.place(x=230, y=70, height=25, width=80)

    def on_delete_room_in_lib(self, *args):
        # 删除库中一个房间的信息
        room_name = self.lib_show_content.selection_get()  # 当前选中房间的名称
        room_list = self.live_room_lib[self.lib_select_combo.get()]
        for one_pair in room_list:
            if room_name == one_pair[0]:
                self.live_room_lib[self.lib_select_combo.get()].remove(one_pair)
                break
        self.lib_select_combo.current(self.lib_select_combo.current())  # 不带参的current返回当前索引
        # 这里是要再选一遍，来更新show_content中的内容

    def on_sending_room_selected(self, *args):
        # 当发送列表中的一个房间被选中时
        if len(self.sending_list_show_content.curselection()) > 0:
            # 因为这个事件在listbox被改变时也能触发，不一定是选中，所以加一个判断
            if len(self.lib_select_combo['values']) == 0:  # 没有库，不能复制过去
                self.copy_room_to_lib_button.configure(state=tkinter.DISABLED)
            else:
                self.copy_room_to_lib_button.configure(state=tkinter.NORMAL)

            self.modify_room_in_sending_list.configure(state=tkinter.NORMAL)
            self.delete_room_in_sending_list.configure(state=tkinter.NORMAL)

            room_name = self.sending_list_show_content.selection_get()  # 当前选中房间的名称
            cur_index = 0  # 当前选中房间的索引
            for i in range(len(self.sending_list)):
                if room_name == self.sending_list[i][0]:
                    cur_index = i
                    break
            if cur_index != 0:
                self.up_button.configure(state=tkinter.NORMAL)
                self.up_to_top_button.configure(state=tkinter.NORMAL)
            else:
                self.up_button.configure(state=tkinter.DISABLED)
                self.up_to_top_button.configure(state=tkinter.DISABLED)
            if cur_index != len(self.sending_list) - 1:
                self.down_button.configure(state=tkinter.NORMAL)
                self.down_to_bottom_button.configure(state=tkinter.NORMAL)
            else:
                self.down_button.configure(state=tkinter.DISABLED)
                self.down_to_bottom_button.configure(state=tkinter.DISABLED)
        else:
            self.copy_room_to_lib_button.configure(state=tkinter.DISABLED)
            self.modify_room_in_sending_list.configure(state=tkinter.DISABLED)
            self.delete_room_in_sending_list.configure(state=tkinter.DISABLED)

            self.up_button.configure(state=tkinter.DISABLED)
            self.up_to_top_button.configure(state=tkinter.DISABLED)
            self.down_button.configure(state=tkinter.DISABLED)
            self.down_to_bottom_button.configure(state=tkinter.DISABLED)

    def on_copy_room_to_lib(self, *args):
        # 将直播间复制到库中
        room_name = self.sending_list_show_content.selection_get()  # 当前选中房间的名称
        cur_index = 0  # 当前选中房间的索引
        for i in range(len(self.sending_list)):
            if room_name == self.sending_list[i][0]:
                cur_index = i
                break
        lib_room_list = self.live_room_lib[self.lib_select_combo.get()]
        for lib_room in lib_room_list:
            if room_name == lib_room[0]:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='名称已存在',
                    parent=self  # 这样才会显示在当前窗口上方
                )
                return
        self.live_room_lib[self.lib_select_combo.get()].append(self.sending_list[cur_index])
        self.lib_select_combo.current(self.lib_select_combo.current())  # 不带参的current返回当前索引
        # 这里是要再选一遍，来更新show_content中的内容

    def on_create_room_in_sending_list(self, *args):
        # 新建一个房间信息，添加到发送列表中
        # 弹出一个界面
        new_window = tkinter.Toplevel()
        new_window.title("添加新房间")
        new_window.attributes('-topmost', True)
        width = 320
        height = 100
        to_left = (new_window.winfo_screenwidth() - width) / 2
        to_top = (new_window.winfo_screenheight() - height) / 2
        # 居中
        new_window.geometry("%dx%d+%d+%d" % (width, height, to_left, to_top))
        new_window.grab_set()  # 这一句使得新窗口捕获所有事件
        new_window.focus_force()  # 获取焦点

        name_label = tkinter.Label(
            new_window,
            text='名称:'
        )
        name_label.place(x=10, y=10, height=20, width=40)
        name_entry = tkinter.Entry(
            new_window
        )
        name_entry.place(x=55, y=10, height=25, width=246)
        name_entry.focus_force()

        # 房间号只能是数字
        def isIntegerValidate(new_str):
            if ' ' in new_str:
                return False
            if len(new_str) == 0:
                return True
            try:
                int(new_str)
                return True
            except ValueError:
                pass
            return False

        registry_validate_command = \
            self.register(isIntegerValidate)  # 一定要这里先注册下面的validatecommand才可以带参
        room_id_label = tkinter.Label(
            new_window,
            text='房间号:'
        )
        room_id_label.place(x=10, y=40, height=20, width=40)
        room_id_entry = tkinter.Entry(
            new_window,
            validate='key',  # 值变化时进行验证
            validatecommand=(registry_validate_command, '%P'),  # 验证函数，要返回True或False，表示是否验证成功
        )
        room_id_entry.place(x=55, y=40, height=25, width=246)

        def on_confirm_clicked(*args):
            name = name_entry.get().strip(' \t\r\n')  # 去除首尾空白符
            room_id = room_id_entry.get().strip('\r\n')
            if len(name) == 0 or len(room_id) == 0:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='名称、房间号不能为空',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
                return
            # 能按下这个按钮肯定是有库的
            already_has = False
            for one_pair in self.sending_list:
                if name == one_pair[0]:
                    already_has = True
                    break
            if already_has:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='名称已存在',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
            else:
                self.sending_list.append((name, room_id))
                # 更新listbox，这里是为了取消选中，虽然好像没什么必要
                self.sending_list_show_content.delete(0, tkinter.END)
                for one_room in self.sending_list:
                    self.sending_list_show_content.insert(tkinter.END, one_room[0])
                # 一些按钮失效
                self.copy_room_to_lib_button.configure(state=tkinter.DISABLED)
                self.modify_room_in_sending_list.configure(state=tkinter.DISABLED)
                self.delete_room_in_sending_list.configure(state=tkinter.DISABLED)

                self.up_button.configure(state=tkinter.DISABLED)
                self.down_button.configure(state=tkinter.DISABLED)
                self.up_to_top_button.configure(state=tkinter.DISABLED)
                self.down_to_bottom_button.configure(state=tkinter.DISABLED)

                new_window.destroy()  # 关闭窗口

        confirm_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='确认',
            style='own.TButton',
            command=on_confirm_clicked
        )
        confirm_button.place(x=140, y=70, height=25, width=80)
        cancel_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='取消',
            style='own.TButton',
            command=new_window.destroy  # 按钮按下，关闭窗口
        )
        cancel_button.place(x=230, y=70, height=25, width=80)

    def on_modify_room_in_sending_list(self, *args):
        # 修改发送列表中一个房间的信息
        room_name = self.sending_list_show_content.selection_get()  # 当前选中房间的名称
        cur_index = 0  # 当前选中房间的索引
        for i in range(len(self.sending_list)):
            if room_name == self.sending_list[i][0]:
                cur_index = i
                break
        # 接下来和创建界面类似，只不过有初始值
        # 弹出一个界面
        new_window = tkinter.Toplevel()
        new_window.title("修改房间信息")
        new_window.attributes('-topmost', True)
        width = 320
        height = 100
        to_left = (new_window.winfo_screenwidth() - width) / 2
        to_top = (new_window.winfo_screenheight() - height) / 2
        # 居中
        new_window.geometry("%dx%d+%d+%d" % (width, height, to_left, to_top))
        new_window.grab_set()  # 这一句使得新窗口捕获所有事件
        new_window.focus_force()  # 获取焦点

        name_label = tkinter.Label(
            new_window,
            text='名称:'
        )
        name_label.place(x=10, y=10, height=20, width=40)
        name_entry = tkinter.Entry(
            new_window
        )
        name_entry.insert(0, self.sending_list[cur_index][0])  # 设置初始值
        name_entry.place(x=55, y=10, height=25, width=246)
        name_entry.focus_force()

        # 房间号只能是数字
        def isIntegerValidate(new_str):
            if ' ' in new_str:
                return False
            if len(new_str) == 0:
                return True
            try:
                int(new_str)
                return True
            except ValueError:
                pass
            return False

        registry_validate_command = \
            self.register(isIntegerValidate)  # 一定要这里先注册下面的validatecommand才可以带参
        room_id_label = tkinter.Label(
            new_window,
            text='房间号:'
        )
        room_id_label.place(x=10, y=40, height=20, width=40)
        room_id_entry = tkinter.Entry(
            new_window,
            validate='key',  # 值变化时进行验证
            validatecommand=(registry_validate_command, '%P'),  # 验证函数，要返回True或False，表示是否验证成功
        )
        room_id_entry.insert(0, self.sending_list[cur_index][1])  # 设置初始值
        room_id_entry.place(x=55, y=40, height=25, width=246)

        def on_confirm_clicked(*args):
            name = name_entry.get().strip(' \t\r\n')  # 去除首尾空白符
            room_id = room_id_entry.get().strip('\r\n')
            if len(name) == 0 or len(room_id) == 0:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='名称、房间号不能为空',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
                return
            # 能按下这个按钮肯定是有库的
            already_has = False
            for i in range(len(self.sending_list)):
                if i != cur_index:
                    if name == self.sending_list[i][0]:
                        already_has = True
                        break
            if already_has:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='名称已存在',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
            else:
                self.sending_list[cur_index] = (name, room_id)
                # 更新listbox
                self.sending_list_show_content.delete(0, tkinter.END)
                for one_room in self.sending_list:
                    self.sending_list_show_content.insert(tkinter.END, one_room[0])
                # 一些按钮失效
                self.copy_room_to_lib_button.configure(state=tkinter.DISABLED)
                self.modify_room_in_sending_list.configure(state=tkinter.DISABLED)
                self.delete_room_in_sending_list.configure(state=tkinter.DISABLED)

                self.up_button.configure(state=tkinter.DISABLED)
                self.down_button.configure(state=tkinter.DISABLED)
                self.up_to_top_button.configure(state=tkinter.DISABLED)
                self.down_to_bottom_button.configure(state=tkinter.DISABLED)

                new_window.destroy()  # 关闭窗口

        confirm_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='确认',
            style='own.TButton',
            command=on_confirm_clicked
        )
        confirm_button.place(x=140, y=70, height=25, width=80)
        cancel_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='取消',
            style='own.TButton',
            command=new_window.destroy  # 按钮按下，关闭窗口
        )
        cancel_button.place(x=230, y=70, height=25, width=80)

    def on_delete_room_in_sending_list(self, *args):
        # 删除发送列表中一个房间的信息
        room_name = self.sending_list_show_content.selection_get()  # 当前选中房间的名称
        for one_pair in self.sending_list:
            if room_name == one_pair[0]:
                self.sending_list.remove(one_pair)
                break
        # 更新listbox
        self.sending_list_show_content.delete(0, tkinter.END)
        for one_room in self.sending_list:
            self.sending_list_show_content.insert(tkinter.END, one_room[0])
        # 一些按钮失效
        self.copy_room_to_lib_button.configure(state=tkinter.DISABLED)
        self.modify_room_in_sending_list.configure(state=tkinter.DISABLED)
        self.delete_room_in_sending_list.configure(state=tkinter.DISABLED)

        self.up_button.configure(state=tkinter.DISABLED)
        self.down_button.configure(state=tkinter.DISABLED)
        self.up_to_top_button.configure(state=tkinter.DISABLED)
        self.down_to_bottom_button.configure(state=tkinter.DISABLED)

    def move_up_in_sending_list(self, *args):
        # 能进到这里肯定不是第一项
        room_name = self.sending_list_show_content.selection_get()  # 当前选中房间的名称
        cur_index = 0  # 当前选中房间的索引
        for i in range(len(self.sending_list)):
            if room_name == self.sending_list[i][0]:
                cur_index = i
                break
        # 交换
        temp = self.sending_list[cur_index - 1]
        self.sending_list[cur_index - 1] = self.sending_list[cur_index]
        self.sending_list[cur_index] = temp

        # 更新listbox
        self.sending_list_show_content.delete(0, tkinter.END)
        for one_room in self.sending_list:
            self.sending_list_show_content.insert(tkinter.END, one_room[0])

        self.sending_list_show_content.select_set(cur_index - 1)  # 再选中原来那个
        self.on_sending_room_selected(args)  # 手动触发一下,,,这个args可能不是很对应

    def up_to_top_in_sending_list(self, *args):
        # 能进到这里肯定不是第一项
        room_name = self.sending_list_show_content.selection_get()  # 当前选中房间的名称
        cur_index = 0  # 当前选中房间的索引
        for i in range(len(self.sending_list)):
            if room_name == self.sending_list[i][0]:
                cur_index = i
                break
        # 前移至顶部
        for i in range(cur_index, 0, -1):
            temp = self.sending_list[i - 1]
            self.sending_list[i - 1] = self.sending_list[i]
            self.sending_list[i] = temp

        # 更新listbox
        self.sending_list_show_content.delete(0, tkinter.END)
        for one_room in self.sending_list:
            self.sending_list_show_content.insert(tkinter.END, one_room[0])

        self.sending_list_show_content.select_set(0)  # 再选中原来那个
        self.on_sending_room_selected(args)  # 手动触发一下,,,这个args可能不是很对应

    def move_down_in_sending_list(self, *args):
        # 能进到这里肯定不是最后一项
        room_name = self.sending_list_show_content.selection_get()  # 当前选中房间的名称
        cur_index = 0  # 当前选中房间的索引
        for i in range(len(self.sending_list)):
            if room_name == self.sending_list[i][0]:
                cur_index = i
                break
        # 交换
        temp = self.sending_list[cur_index + 1]
        self.sending_list[cur_index + 1] = self.sending_list[cur_index]
        self.sending_list[cur_index] = temp

        # 更新listbox
        self.sending_list_show_content.delete(0, tkinter.END)
        for one_room in self.sending_list:
            self.sending_list_show_content.insert(tkinter.END, one_room[0])

        self.sending_list_show_content.select_set(cur_index + 1)  # 再选中原来那个
        self.on_sending_room_selected(args)  # 手动触发一下,,,这个args可能不是很对应

    def down_to_bottom_in_sending_list(self, *args):
        # 能进到这里肯定不是最后一项
        room_name = self.sending_list_show_content.selection_get()  # 当前选中房间的名称
        cur_index = 0  # 当前选中房间的索引
        for i in range(len(self.sending_list)):
            if room_name == self.sending_list[i][0]:
                cur_index = i
                break
        # 交换
        for i in range(cur_index, len(self.sending_list) - 1):
            temp = self.sending_list[i + 1]
            self.sending_list[i + 1] = self.sending_list[i]
            self.sending_list[i] = temp

        # 更新listbox
        self.sending_list_show_content.delete(0, tkinter.END)
        for one_room in self.sending_list:
            self.sending_list_show_content.insert(tkinter.END, one_room[0])

        self.sending_list_show_content.select_set(len(self.sending_list) - 1)  # 再选中原来那个
        self.on_sending_room_selected(args)  # 手动触发一下,,,这个args可能不是很对应


class WordFixSettingPage(BaseFrame):
    def __init__(self, parent, controller, word_fix_lib):
        parent.update()  # update之后才可以获取到最新的宽度和高度
        BaseFrame.__init__(
            self,
            parent,
            height=parent.winfo_height(),
            width=parent.winfo_width()
        )
        self.parent = parent
        self.controller = controller
        self.word_fix_lib = word_fix_lib  # 一个字典，key为前后缀名(不能为空，创建时限定)，value为具体前后缀
        self.selected_word_fix_list = [('【', '】'), ('', '')]  # 用一个列表保存，[(前缀，后缀)，...]，给一个默认的
        self.create_widgets()

    def create_widgets(self):
        # 从上往下设计
        self.lib_select_group = tkinter.LabelFrame(
            self,
            text='已存前后缀库目录'
        )
        self.lib_select_group.place(x=10, y=10, height=90, width=780)

        self.combostyle = tkinter.ttk.Style()
        self.combostyle.configure(  # 定义一个style，后面能用
            'own.TCombobox'
        )
        # 不是很会设置Combobox，网上教程都不太全，这里简单设置一个theme
        self.combostyle.theme_use('xpnative')
        # print(combostyle.element_names())
        # print(combostyle.element_options('Combobox.rightdownarrow'))

        self.word_fix_lib_tracer = tkinter.StringVar()
        self.word_fix_lib_tracer.trace("w", self.on_lib_selected)  # 值被修改时调用函数
        self.lib_select_combo = ttk.Combobox(
            self.lib_select_group,
            takefocus=0,  # 取消焦点
            state='readonly',
            style='own.TCombobox',
            values=list(self.word_fix_lib.keys()),
            textvariable=self.word_fix_lib_tracer
        )
        self.lib_select_combo.place(x=10, y=5, height=24, width=540)
        # 下拉框选择之后，调用相应函数
        # 还是用StringVar好，这样初始化的时候的设置也能捕捉到
        # self.lib_select_combo.bind("<<ComboboxSelected>>", self.on_lib_selected)
        # 然后这个有个初始选择，选择第一个，这个设置放在下面两个show_content设置完之后
        # 因为绑定了StringVar，绑定了相应的函数，函数会调用...

        self.buttonstyle = tkinter.ttk.Style()
        self.buttonstyle.configure(  # 定义一个style，后面能用
            'own.TButton'
        )
        # 简单设置一个theme
        self.buttonstyle.theme_use('xpnative')
        self.create_lib_button = ttk.Button(  # 注意是ttk的button
            self.lib_select_group,
            text='新建',
            style='own.TButton',
            command=self.on_lib_create
        )
        self.create_lib_button.place(x=560, y=3, height=28, width=100)

        self.delete_lib_button = ttk.Button(  # 注意是ttk的button
            self.lib_select_group,
            text='删除',
            style='own.TButton',
            command=self.on_lib_delete
        )
        self.delete_lib_button.place(x=670, y=3, height=28, width=100)
        if len(self.lib_select_combo['values']) == 0:
            self.delete_lib_button.configure(state=tkinter.DISABLED)

        # 示例
        content_sample_label = tkinter.Label(
            self.lib_select_group,
            text='示例:'
        )
        content_sample_label.place(x=0, y=35, height=28, width=50)

        self.content_sample_tracer = tkinter.StringVar()
        self.content_sample_tracer.trace("w", self.on_content_sample_changed)  # 值被修改时调用函数
        self.content_sample_entry = tkinter.Entry(
            self.lib_select_group,
            textvariable=self.content_sample_tracer
        )
        self.content_sample_entry.place(x=50, y=35, height=28, width=100)

        ##########################################
        # 下面是显示库中内容了
        self.lib_show_group = tkinter.LabelFrame(
            self,
            text='前后缀库'
        )
        self.lib_show_group.place(x=10, y=100, height=330, width=335)

        self.lib_show_content = tkinter.Listbox(
            self.lib_show_group,
            activestyle='none',  # 默认是有下划线的
            bd=1,
            highlightthickness=0,
            # relief='flat'  # 用默认sunken
        )
        self.lib_show_content.place(x=10, y=10, height=230, width=315)
        self.lib_show_content.bind('<<ListboxSelect>>', self.on_lib_word_fix_selected)

        self.add_word_fix_to_cur_list_button = ttk.Button(  # 注意是ttk的button
            self.lib_show_group,
            text='添加前后缀至本次使用列表->',
            style='own.TButton',
            command=self.on_add_word_fix_to_cur_list
        )
        self.add_word_fix_to_cur_list_button.place(x=10, y=242, height=28, width=315)

        self.create_word_fix_in_lib = ttk.Button(  # 注意是ttk的button
            self.lib_show_group,
            text='新建',
            style='own.TButton',
            command=self.on_create_word_fix_in_lib
        )
        self.create_word_fix_in_lib.place(x=10, y=275, height=28, width=100)

        self.modify_word_fix_in_lib = ttk.Button(  # 注意是ttk的button
            self.lib_show_group,
            text='修改',
            style='own.TButton',
            command=self.on_modify_word_fix_in_lib
        )
        self.modify_word_fix_in_lib.place(x=115, y=275, height=28, width=105)

        self.delete_word_fix_in_lib = ttk.Button(  # 注意是ttk的button
            self.lib_show_group,
            text='删除',
            style='own.TButton',
            command=self.on_delete_word_fix_in_lib
        )
        self.delete_word_fix_in_lib.place(x=225, y=275, height=28, width=100)

        self.add_word_fix_to_cur_list_button.configure(state=tkinter.DISABLED)  # 选择一个直播间后才能进行添加
        self.create_word_fix_in_lib.configure(state=tkinter.DISABLED)  # 开始可能没有库，没有库不能新建
        self.modify_word_fix_in_lib.configure(state=tkinter.DISABLED)  # 也要先选中
        self.delete_word_fix_in_lib.configure(state=tkinter.DISABLED)  # 也要先选中

        ##################################################
        # 下面是当前已添加的直播间
        self.selected_word_fix_group = tkinter.LabelFrame(
            self,
            text='本次使用的前后缀(先后顺序对应切换顺序)'
        )
        self.selected_word_fix_group.place(x=375, y=100, height=330, width=380)

        self.selected_word_fix_list_show_content = tkinter.Listbox(
            self.selected_word_fix_group,
            activestyle='none',  # 默认是有下划线的
            bd=1,
            highlightthickness=0,
            # relief='flat'  # 用默认sunken
        )
        self.selected_word_fix_list_show_content.place(x=10, y=10, height=230, width=315)
        self.selected_word_fix_list_show_content.bind('<<ListboxSelect>>', self.on_word_fix_in_selected_list_selected)

        self.copy_word_fix_to_lib_button = ttk.Button(  # 注意是ttk的button
            self.selected_word_fix_group,
            text='<-复制前后缀至库中',
            style='own.TButton',
            command=self.on_copy_word_fix_to_lib
        )
        self.copy_word_fix_to_lib_button.place(x=10, y=242, height=28, width=315)

        self.create_word_fix_in_selected_word_fix_list = ttk.Button(  # 注意是ttk的button
            self.selected_word_fix_group,
            text='新建',
            style='own.TButton',
            command=self.on_create_word_fix_in_selected_word_fix_list
        )
        self.create_word_fix_in_selected_word_fix_list.place(x=10, y=275, height=28, width=100)

        self.modify_word_fix_in_selected_word_fix_list = ttk.Button(  # 注意是ttk的button
            self.selected_word_fix_group,
            text='修改',
            style='own.TButton',
            command=self.on_modify_word_fix_in_selected_word_fix_list
        )
        self.modify_word_fix_in_selected_word_fix_list.place(x=115, y=275, height=28, width=105)

        self.delete_word_fix_in_selected_word_fix_list = ttk.Button(  # 注意是ttk的button
            self.selected_word_fix_group,
            text='删除',
            style='own.TButton',
            command=self.on_delete_word_fix_in_selected_word_fix_list
        )
        self.delete_word_fix_in_selected_word_fix_list.place(x=225, y=275, height=28, width=100)

        self.copy_word_fix_to_lib_button.configure(state=tkinter.DISABLED)  # 选择一个直播间后才能进行复制
        self.modify_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)  # 也要先选中
        self.delete_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)  # 也要先选中

        # 还有一排小"按钮"
        self.up_img = tkinter.PhotoImage(
            file='./resource/figure/up.png'
        )
        self.up_button = tkinter.Button(
            self.selected_word_fix_group,
            image=self.up_img,
            command=self.move_up_in_selected_word_fix_list
        )
        self.up_button.place(x=332, y=40, height=36, width=36)

        self.down_img = tkinter.PhotoImage(
            file='./resource/figure/down.png'
        )
        self.down_button = tkinter.Button(
            self.selected_word_fix_group,
            image=self.down_img,
            command=self.move_down_in_selected_word_fix_list
        )
        self.down_button.place(x=332, y=80, height=36, width=36)

        self.up_to_top_img = tkinter.PhotoImage(
            file='./resource/figure/up_to_top.png'
        )
        self.up_to_top_button = tkinter.Button(
            self.selected_word_fix_group,
            image=self.up_to_top_img,
            command=self.up_to_top_in_selected_word_fix_list
        )
        self.up_to_top_button.place(x=332, y=130, height=36, width=36)

        self.down_to_buttom_img = tkinter.PhotoImage(
            file='./resource/figure/down_to_buttom.png'
        )
        self.down_to_bottom_button = tkinter.Button(
            self.selected_word_fix_group,
            image=self.down_to_buttom_img,
            command=self.down_to_bottom_in_selected_word_fix_list
        )
        self.down_to_bottom_button.place(x=332, y=170, height=36, width=36)

        self.up_button.configure(state=tkinter.DISABLED)
        self.down_button.configure(state=tkinter.DISABLED)
        self.up_to_top_button.configure(state=tkinter.DISABLED)
        self.down_to_bottom_button.configure(state=tkinter.DISABLED)

        # 这个初始化选择要放在两个show_content、上面这四个按钮之后
        # 因为StringVar绑定了函数，函数里要用到
        if len(self.word_fix_lib) > 0:
            # 选中第一个库
            self.lib_select_combo.current(0)
        else:
            self.content_sample_entry.delete(0, tkinter.END)
            self.content_sample_entry.insert(0, 'xx')  # 默认示例

        ##############################################
        # 最后再一些按钮，到上一页设定和完成设定
        self.goto_previous_page_button = ttk.Button(  # 注意是ttk的button
            self,
            text='上一页',
            style='own.TButton',
            command=self.goto_previous_page
        )
        self.goto_previous_page_button.place(x=560, y=440, height=28, width=110)

        self.setting_finish_button = ttk.Button(  # 注意是ttk的button
            self,
            text='完成',
            style='own.TButton',
            command=self.setting_finish
        )
        self.setting_finish_button.place(x=680, y=440, height=28, width=110)

    def get_word_fix_lib(self):
        return self.word_fix_lib

    def get_content_sample(self):
        return self.content_sample_entry.get()

    def get_word_fix_list(self):
        return self.selected_word_fix_list

    def goto_previous_page(self):
        self.controller.goto_previous_page()

    def setting_finish(self):
        self.controller.finish()

    def on_content_sample_changed(self, *args):
        content_sample = self.content_sample_entry.get()

        if len(self.lib_select_combo['values']) == 0:  # 没有库，但有当前前后缀信息，要改
            # 当前选中列表也要更新
            self.selected_word_fix_list_show_content.delete(0, tkinter.END)
            for i in range(0, len(self.selected_word_fix_list)):  # 这里是没有content sample的
                self.selected_word_fix_list_show_content.insert(
                    tkinter.END,
                    self.selected_word_fix_list[i][0] + content_sample + self.selected_word_fix_list[i][1]
                )
            # 一些按钮失效
            self.create_word_fix_in_lib.configure(state=tkinter.DISABLED)
            self.add_word_fix_to_cur_list_button.configure(state=tkinter.DISABLED)
            self.modify_word_fix_in_lib.configure(state=tkinter.DISABLED)
            self.delete_word_fix_in_lib.configure(state=tkinter.DISABLED)

            self.copy_word_fix_to_lib_button.configure(state=tkinter.DISABLED)
            self.modify_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)
            self.delete_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)

            self.up_button.configure(state=tkinter.DISABLED)
            self.up_to_top_button.configure(state=tkinter.DISABLED)
            self.down_button.configure(state=tkinter.DISABLED)
            self.down_to_bottom_button.configure(state=tkinter.DISABLED)

            return

        word_fix_list = self.word_fix_lib[self.lib_select_combo.get()]
        word_fix_list[0] = content_sample
        # 然后根据这个更新listbox
        self.lib_show_content.delete(0, tkinter.END)
        for i in range(1, len(word_fix_list)):
            self.lib_show_content.insert(tkinter.END,
                                         word_fix_list[i][0] + content_sample + word_fix_list[i][1])

        # 一些按钮失效
        self.add_word_fix_to_cur_list_button.configure(state=tkinter.DISABLED)
        self.modify_word_fix_in_lib.configure(state=tkinter.DISABLED)
        self.delete_word_fix_in_lib.configure(state=tkinter.DISABLED)
        # 当前选中列表也要更新
        self.selected_word_fix_list_show_content.delete(0, tkinter.END)
        for i in range(0, len(self.selected_word_fix_list)):  # 这里是没有content sample的
            self.selected_word_fix_list_show_content.insert(
                tkinter.END,
                self.selected_word_fix_list[i][0]+content_sample+self.selected_word_fix_list[i][1]
            )
        # 一些按钮失效
        self.copy_word_fix_to_lib_button.configure(state=tkinter.DISABLED)
        self.modify_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)
        self.delete_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)

        self.up_button.configure(state=tkinter.DISABLED)
        self.up_to_top_button.configure(state=tkinter.DISABLED)
        self.down_button.configure(state=tkinter.DISABLED)
        self.down_to_bottom_button.configure(state=tkinter.DISABLED)

    def on_lib_selected(self, *args):
        if len(self.lib_select_combo['values']) == 0:  # 没有元素可以选了
            content_sample = self.content_sample_entry.get()
            self.content_sample_entry.delete(0,tkinter.END)
            self.content_sample_entry.insert(0, content_sample)  # 这里这样做是为了调用on_content_sample_changed
            self.lib_show_content.delete(0, tkinter.END)
            self.create_word_fix_in_lib.configure(state=tkinter.DISABLED)  # 没有库不能新建
            self.lib_show_content.configure(state=tkinter.DISABLED)
            return
        self.create_word_fix_in_lib.configure(state=tkinter.NORMAL)
        self.lib_show_content.configure(state=tkinter.NORMAL)
        word_fix_list = self.word_fix_lib[self.lib_select_combo.get()]
        content_sample = word_fix_list[0]  # 第一项是示例
        self.content_sample_entry.delete(0, tkinter.END)
        self.content_sample_entry.insert(0, content_sample)
        # entry改变了，会调用上面的on_content_sample_changed，会更新listbox

    def on_lib_create(self, *args):
        # 创建一个库，弹出一个界面
        new_window = tkinter.Toplevel()
        new_window.title("添加新前后缀库")
        new_window.attributes('-topmost', True)
        width = 320
        height = 100
        to_left = (new_window.winfo_screenwidth() - width) / 2
        to_top = (new_window.winfo_screenheight() - height) / 2
        # 居中
        new_window.geometry("%dx%d+%d+%d" % (width, height, to_left, to_top))
        new_window.grab_set()  # 这一句使得新窗口捕获所有事件
        new_window.focus_force()  # 获取焦点

        name_label = tkinter.Label(
            new_window,
            text='库名称:'
        )
        name_label.place(x=10, y=10, height=20, width=40)
        name_entry = tkinter.Entry(
            new_window
        )
        name_entry.place(x=55, y=10, height=25, width=246)
        name_entry.focus_force()

        content_sample_label = tkinter.Label(
            new_window,
            text='示例:'
        )
        content_sample_label.place(x=10, y=40, height=20, width=40)
        content_sample_entry = tkinter.Entry(
            new_window
        )
        content_sample_entry.insert(0, 'xx')  # 默认'xx'
        content_sample_entry.place(x=55, y=40, height=25, width=246)

        def on_confirm_clicked(*args):
            name = name_entry.get().strip(' \t\r\n')  # 去除首尾空白符
            content_sample = content_sample_entry.get().strip('\r\n')
            if len(name) == 0 or len(content_sample) == 0:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='名称、示例不能只由空白符构成',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
            elif name in self.lib_select_combo['values']:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='库名已存在',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
            elif ',' in name:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='库名不能带有\',\'',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
            else:
                self.word_fix_lib[name] = [content_sample]

                self.lib_select_combo['values'] = tuple(self.lib_select_combo['values']) + (name,)
                self.lib_select_combo.current(len(self.lib_select_combo['values']) - 1)  # 显示最新的
                self.delete_lib_button.configure(state=tkinter.NORMAL)
                new_window.destroy()  # 关闭窗口

        confirm_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='确认',
            style='own.TButton',
            command=on_confirm_clicked
        )
        confirm_button.place(x=140, y=70, height=25, width=80)
        cancel_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='取消',
            style='own.TButton',
            command=new_window.destroy  # 按钮按下，关闭窗口
        )
        cancel_button.place(x=230, y=70, height=25, width=80)

    def on_lib_delete(self, *args):
        # 删除一个库
        # 这里直接用delete好像删不掉
        all_libs = self.lib_select_combo['values']
        delete_index = all_libs.index(self.lib_select_combo.get())  # 元组里如果没找到该元素会抛出异常，但这里肯定能找到
        self.lib_select_combo['values'] = all_libs[:delete_index] + all_libs[delete_index + 1:]
        del self.word_fix_lib[self.lib_select_combo.get()]  # 字典的删除
        if len(self.lib_select_combo['values']) > 0:
            # 选中第一项
            self.lib_select_combo.current(0)
        else:
            self.lib_select_combo.set("")
            self.delete_lib_button.configure(state=tkinter.DISABLED)
        # print("delete")

    def on_lib_word_fix_selected(self, event):
        # 当库中的一个前后缀被选中时
        if len(self.lib_show_content.curselection()) > 0:
            # 因为这个事件在listbox被改变时也能触发，不一定是选中，所以加一个判断
            self.add_word_fix_to_cur_list_button.configure(state=tkinter.NORMAL)
            self.modify_word_fix_in_lib.configure(state=tkinter.NORMAL)
            self.delete_word_fix_in_lib.configure(state=tkinter.NORMAL)
        else:
            self.add_word_fix_to_cur_list_button.configure(state=tkinter.DISABLED)
            self.modify_word_fix_in_lib.configure(state=tkinter.DISABLED)
            self.delete_word_fix_in_lib.configure(state=tkinter.DISABLED)

    def on_add_word_fix_to_cur_list(self, *args):
        # 添加一个本次使用的前后缀
        complete_sentence = self.lib_show_content.selection_get()  # 当前选中的前后缀，包含示例
        word_fix = re.split(self.content_sample_entry.get(), complete_sentence, 1)

        word_fix_list = self.word_fix_lib[self.lib_select_combo.get()]
        cur_index = 0  # 当前选中前后缀的索引
        for i in range(len(word_fix_list)):
            if word_fix[0] == word_fix_list[i][0] and word_fix[1] == word_fix_list[i][1]:
                cur_index = i
                break
        for selected_word_fix in self.selected_word_fix_list:  # 这里没有content sample
            if word_fix[0] == selected_word_fix[0] and word_fix[1] == selected_word_fix[1]:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='前后缀已存在',
                    parent=self  # 这样才会显示在当前窗口上方
                )
                return
        self.selected_word_fix_list.append(word_fix_list[cur_index])
        # 更新listbox
        self.selected_word_fix_list_show_content.delete(0, tkinter.END)
        for i in range(0, len(self.selected_word_fix_list)):  # 这里是没有content sample的
            self.selected_word_fix_list_show_content.insert(
                tkinter.END,
                self.selected_word_fix_list[i][0] + self.content_sample_entry.get() + self.selected_word_fix_list[i][1]
            )
        # 一些按钮失效
        self.copy_word_fix_to_lib_button.configure(state=tkinter.DISABLED)
        self.modify_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)
        self.delete_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)

    def on_create_word_fix_in_lib(self, *args):
        # 新建一个前后缀信息，添加到当前库中
        # 弹出一个界面
        new_window = tkinter.Toplevel()
        new_window.title("添加新前后缀")
        new_window.attributes('-topmost', True)
        width = 320
        height = 100
        to_left = (new_window.winfo_screenwidth() - width) / 2
        to_top = (new_window.winfo_screenheight() - height) / 2
        # 居中
        new_window.geometry("%dx%d+%d+%d" % (width, height, to_left, to_top))
        new_window.grab_set()  # 这一句使得新窗口捕获所有事件
        new_window.focus_force()  # 获取焦点

        prefix_label = tkinter.Label(
            new_window,
            text='前缀:'
        )
        prefix_label.place(x=10, y=10, height=20, width=40)
        prefix_entry = tkinter.Entry(
            new_window
        )
        prefix_entry.place(x=55, y=10, height=25, width=246)
        prefix_entry.focus_force()

        postfix_label = tkinter.Label(
            new_window,
            text='后缀:'
        )
        postfix_label.place(x=10, y=40, height=20, width=40)
        postfix_entry = tkinter.Entry(
            new_window
        )
        postfix_entry.place(x=55, y=40, height=25, width=246)

        def on_confirm_clicked(*args):
            prefix = prefix_entry.get().strip('\r\n')
            postfix = postfix_entry.get().strip('\r\n')
            # 能按下这个按钮肯定是有库的
            already_has = False
            word_fix_list = self.word_fix_lib[self.lib_select_combo.get()]
            for i in range(1, len(word_fix_list)):  # 第一项是content sample，跳过
                if prefix == word_fix_list[i][0] and postfix == word_fix_list[i][1]:
                    already_has = True
                    break
            if already_has:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='前后缀已存在',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
            else:
                # insert好像没用
                self.word_fix_lib[self.lib_select_combo.get()].append((prefix, postfix))
                self.lib_select_combo.current(self.lib_select_combo.current())  # 不带参的current返回当前索引
                # 这里是要再选一遍，来更新show_content中的内容
                new_window.destroy()  # 关闭窗口

        confirm_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='确认',
            style='own.TButton',
            command=on_confirm_clicked
        )
        confirm_button.place(x=140, y=70, height=25, width=80)
        cancel_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='取消',
            style='own.TButton',
            command=new_window.destroy  # 按钮按下，关闭窗口
        )
        cancel_button.place(x=230, y=70, height=25, width=80)

    def on_modify_word_fix_in_lib(self, *args):
        # 修改库中一个前后缀的信息
        complete_sentence = self.lib_show_content.selection_get()  # 当前选中的一个前后缀
        word_fix = re.split(self.content_sample_entry.get(), complete_sentence, 1)
        word_fix_list = self.word_fix_lib[self.lib_select_combo.get()]
        cur_index = 0  # 当前选中前后缀的索引
        for i in range(1, len(word_fix_list)):
            if word_fix[0] == word_fix_list[i][0] and word_fix[1] == word_fix_list[i][1]:
                cur_index = i
                break
        # 接下来和创建界面类似，只不过有初始值
        # 弹出一个界面
        new_window = tkinter.Toplevel()
        new_window.title("修改前后缀")
        new_window.attributes('-topmost', True)
        width = 320
        height = 100
        to_left = (new_window.winfo_screenwidth() - width) / 2
        to_top = (new_window.winfo_screenheight() - height) / 2
        # 居中
        new_window.geometry("%dx%d+%d+%d" % (width, height, to_left, to_top))
        new_window.grab_set()  # 这一句使得新窗口捕获所有事件
        new_window.focus_force()  # 获取焦点

        prefix_label = tkinter.Label(
            new_window,
            text='前缀:'
        )
        prefix_label.place(x=10, y=10, height=20, width=40)
        prefix_entry = tkinter.Entry(
            new_window
        )
        prefix_entry.insert(0, word_fix_list[cur_index][0])  # 设置初始值
        prefix_entry.place(x=55, y=10, height=25, width=246)
        prefix_entry.focus_force()

        postfix_label = tkinter.Label(
            new_window,
            text='后缀:'
        )
        postfix_label.place(x=10, y=40, height=20, width=40)
        postfix_entry = tkinter.Entry(
            new_window
        )
        postfix_entry.insert(0, word_fix_list[cur_index][1])  # 设置初始值
        postfix_entry.place(x=55, y=40, height=25, width=246)

        def on_confirm_clicked(*args):
            prefix = prefix_entry.get().strip('\r\n')
            postfix = postfix_entry.get().strip('\r\n')
            # 能按下这个按钮肯定是有库的
            already_has = False
            for i in range(1, len(word_fix_list)):  # 第一项是content sample，跳过
                if i != cur_index:
                    if prefix == word_fix_list[i][0] and postfix == word_fix_list[i][1]:
                        already_has = True
                        break
            if already_has:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='前后缀已存在',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
            else:
                # insert好像没用
                self.word_fix_lib[self.lib_select_combo.get()][cur_index] = (prefix, postfix)
                self.lib_select_combo.current(self.lib_select_combo.current())  # 不带参的current返回当前索引
                # 这里是要再选一遍，来更新show_content中的内容
                new_window.destroy()  # 关闭窗口

        confirm_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='确认',
            style='own.TButton',
            command=on_confirm_clicked
        )
        confirm_button.place(x=140, y=70, height=25, width=80)
        cancel_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='取消',
            style='own.TButton',
            command=new_window.destroy  # 按钮按下，关闭窗口
        )
        cancel_button.place(x=230, y=70, height=25, width=80)

    def on_delete_word_fix_in_lib(self, *args):
        # 删除库中一个前后缀的信息
        complete_sentence = self.lib_show_content.selection_get()  # 当前选中的一个前后缀
        word_fix = re.split(self.content_sample_entry.get(), complete_sentence, 1)
        word_fix_list = self.word_fix_lib[self.lib_select_combo.get()]
        for i in range(1, len(word_fix_list)):
            if word_fix[0] == word_fix_list[i][0] and word_fix[1] == word_fix_list[i][1]:
                self.word_fix_lib[self.lib_select_combo.get()].remove(word_fix_list[i])
                break
        self.lib_select_combo.current(self.lib_select_combo.current())  # 不带参的current返回当前索引
        # 这里是要再选一遍，来更新show_content中的内容

    def on_word_fix_in_selected_list_selected(self, *args):
        # 当前前后缀列表中的一个前后缀被选中时
        if len(self.selected_word_fix_list_show_content.curselection()) > 0:
            # 因为这个事件在listbox被改变时也能触发，不一定是选中，所以加一个判断
            if len(self.lib_select_combo['values']) == 0:  # 没有库不能选
                self.copy_word_fix_to_lib_button.configure(state=tkinter.DISABLED)
            else:
                self.copy_word_fix_to_lib_button.configure(state=tkinter.NORMAL)
            self.modify_word_fix_in_selected_word_fix_list.configure(state=tkinter.NORMAL)
            self.delete_word_fix_in_selected_word_fix_list.configure(state=tkinter.NORMAL)

            complete_sentence = self.selected_word_fix_list_show_content.selection_get()  # 当前选中的前后缀
            word_fix = re.split(self.content_sample_entry.get(), complete_sentence, 1)
            cur_index = 0  # 当前选中前后缀的索引
            for i in range(len(self.selected_word_fix_list)):  # 这里没有content sample
                if word_fix[0] == self.selected_word_fix_list[i][0] and word_fix[1] == self.selected_word_fix_list[i][1]:
                    cur_index = i
                    break
            if cur_index != 0:
                self.up_button.configure(state=tkinter.NORMAL)
                self.up_to_top_button.configure(state=tkinter.NORMAL)
            else:
                self.up_button.configure(state=tkinter.DISABLED)
                self.up_to_top_button.configure(state=tkinter.DISABLED)
            if cur_index != len(self.selected_word_fix_list) - 1:
                self.down_button.configure(state=tkinter.NORMAL)
                self.down_to_bottom_button.configure(state=tkinter.NORMAL)
            else:
                self.down_button.configure(state=tkinter.DISABLED)
                self.down_to_bottom_button.configure(state=tkinter.DISABLED)
        else:
            self.copy_word_fix_to_lib_button.configure(state=tkinter.DISABLED)
            self.modify_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)
            self.delete_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)

            self.up_button.configure(state=tkinter.DISABLED)
            self.up_to_top_button.configure(state=tkinter.DISABLED)
            self.down_button.configure(state=tkinter.DISABLED)
            self.down_to_bottom_button.configure(state=tkinter.DISABLED)

    def on_copy_word_fix_to_lib(self, *args):
        # 将前后缀复制到库中
        complete_sentence = self.selected_word_fix_list_show_content.selection_get()  # 当前选中的前后缀
        word_fix = re.split(self.content_sample_entry.get(), complete_sentence, 1)
        prefix = word_fix[0]
        postfix = word_fix[1]
        cur_index = 0  # 当前选中前后缀的索引
        for i in range(len(self.selected_word_fix_list)):  # 这里没有content sample
            if word_fix[0] == self.selected_word_fix_list[i][0] and word_fix[1] == self.selected_word_fix_list[i][1]:
                cur_index = i
                break
        lib_word_fix_list = self.word_fix_lib[self.lib_select_combo.get()]
        for i in range(1, len(lib_word_fix_list)):  # 第一项是content sample，跳过
            if prefix == lib_word_fix_list[i][0] and postfix == lib_word_fix_list[i][1]:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='前后缀已存在',
                    parent=self  # 这样才会显示在当前窗口上方
                )
                return
        self.word_fix_lib[self.lib_select_combo.get()].append(self.selected_word_fix_list[cur_index])
        self.lib_select_combo.current(self.lib_select_combo.current())  # 不带参的current返回当前索引
        # 这里是要再选一遍，来更新show_content中的内容

    def on_create_word_fix_in_selected_word_fix_list(self, *args):
        # 新建一个前后缀信息，添加到本次前后缀列表
        # 弹出一个界面
        new_window = tkinter.Toplevel()
        new_window.title("添加新前后缀")
        new_window.attributes('-topmost', True)
        width = 320
        height = 100
        to_left = (new_window.winfo_screenwidth() - width) / 2
        to_top = (new_window.winfo_screenheight() - height) / 2
        # 居中
        new_window.geometry("%dx%d+%d+%d" % (width, height, to_left, to_top))
        new_window.grab_set()  # 这一句使得新窗口捕获所有事件
        new_window.focus_force()  # 获取焦点

        prefix_label = tkinter.Label(
            new_window,
            text='前缀:'
        )
        prefix_label.place(x=10, y=10, height=20, width=40)
        prefix_entry = tkinter.Entry(
            new_window
        )
        prefix_entry.place(x=55, y=10, height=25, width=246)
        prefix_entry.focus_force()

        postfix_label = tkinter.Label(
            new_window,
            text='后缀:'
        )
        postfix_label.place(x=10, y=40, height=20, width=40)
        postfix_entry = tkinter.Entry(
            new_window
        )
        postfix_entry.place(x=55, y=40, height=25, width=246)

        def on_confirm_clicked(*args):
            prefix = prefix_entry.get().strip('\r\n')
            postfix = postfix_entry.get().strip('\r\n')
            # 能按下这个按钮肯定是有库的
            already_has = False
            for one_pair in self.selected_word_fix_list:  # 这里没有content sample
                if prefix == one_pair[0] and postfix == one_pair[1]:
                    already_has = True
                    break
            if already_has:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='前后缀已存在',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
            else:
                self.selected_word_fix_list.append((prefix, postfix))
                # 更新listbox，这里是为了取消选中，虽然好像没什么必要
                self.selected_word_fix_list_show_content.delete(0, tkinter.END)
                for one_word_fix in self.selected_word_fix_list:
                    self.selected_word_fix_list_show_content.insert(
                        tkinter.END,
                        one_word_fix[0] + self.content_sample_entry.get() + one_word_fix[1])
                # 一些按钮失效
                self.copy_word_fix_to_lib_button.configure(state=tkinter.DISABLED)
                self.modify_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)
                self.delete_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)

                self.up_button.configure(state=tkinter.DISABLED)
                self.down_button.configure(state=tkinter.DISABLED)
                self.up_to_top_button.configure(state=tkinter.DISABLED)
                self.down_to_bottom_button.configure(state=tkinter.DISABLED)

                new_window.destroy()  # 关闭窗口

        confirm_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='确认',
            style='own.TButton',
            command=on_confirm_clicked
        )
        confirm_button.place(x=140, y=70, height=25, width=80)
        cancel_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='取消',
            style='own.TButton',
            command=new_window.destroy  # 按钮按下，关闭窗口
        )
        cancel_button.place(x=230, y=70, height=25, width=80)

    def on_modify_word_fix_in_selected_word_fix_list(self, *args):
        # 修改当前前后缀列表中一个前后缀的信息
        complete_sentence = self.selected_word_fix_list_show_content.selection_get()  # 当前选中的前后缀
        word_fix = re.split(self.content_sample_entry.get(), complete_sentence, 1)
        word_fix_list = self.selected_word_fix_list
        cur_index = 0  # 当前选中前后缀的索引
        for i in range(0, len(word_fix_list)):  # 这里没有content sample
            if word_fix[0] == word_fix_list[i][0] and word_fix[1] == word_fix_list[i][1]:
                cur_index = i
                break
        # 接下来和创建界面类似，只不过有初始值
        # 弹出一个界面
        new_window = tkinter.Toplevel()
        new_window.title("修改前后缀信息")
        new_window.attributes('-topmost', True)
        width = 320
        height = 100
        to_left = (new_window.winfo_screenwidth() - width) / 2
        to_top = (new_window.winfo_screenheight() - height) / 2
        # 居中
        new_window.geometry("%dx%d+%d+%d" % (width, height, to_left, to_top))
        new_window.grab_set()  # 这一句使得新窗口捕获所有事件
        new_window.focus_force()  # 获取焦点

        prefix_label = tkinter.Label(
            new_window,
            text='前缀:'
        )
        prefix_label.place(x=10, y=10, height=20, width=40)
        prefix_entry = tkinter.Entry(
            new_window
        )
        prefix_entry.insert(0, self.selected_word_fix_list[cur_index][0])  # 设置初始值
        prefix_entry.place(x=55, y=10, height=25, width=246)
        prefix_entry.focus_force()

        postfix_label = tkinter.Label(
            new_window,
            text='后缀:'
        )
        postfix_label.place(x=10, y=40, height=20, width=40)
        postfix_entry = tkinter.Entry(
            new_window
        )
        postfix_entry.insert(0, self.selected_word_fix_list[cur_index][1])  # 设置初始值
        postfix_entry.place(x=55, y=40, height=25, width=246)

        def on_confirm_clicked(*args):
            prefix = prefix_entry.get().strip('\r\n')
            postfix = postfix_entry.get().strip('\r\n')
            # 能按下这个按钮肯定是有库的
            already_has = False
            for i in range(len(self.selected_word_fix_list)):
                if i != cur_index:
                    if prefix == self.selected_word_fix_list[i][0] and postfix == self.selected_word_fix_list[i][1]:
                        already_has = True
                        break
            if already_has:
                tkinter.messagebox.showwarning(
                    title='提示',
                    message='前后缀已存在',
                    parent=new_window  # 这样才会显示在当前窗口上方
                )
            else:
                self.selected_word_fix_list[cur_index] = (prefix, postfix)
                # 更新listbox
                self.selected_word_fix_list_show_content.delete(0, tkinter.END)
                for one_word_fix in self.selected_word_fix_list:
                    self.selected_word_fix_list_show_content.insert(
                        tkinter.END,
                        one_word_fix[0] + self.content_sample_entry.get() + one_word_fix[1])
                # 一些按钮失效
                self.copy_word_fix_to_lib_button.configure(state=tkinter.DISABLED)
                self.modify_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)
                self.delete_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)

                self.up_button.configure(state=tkinter.DISABLED)
                self.down_button.configure(state=tkinter.DISABLED)
                self.up_to_top_button.configure(state=tkinter.DISABLED)
                self.down_to_bottom_button.configure(state=tkinter.DISABLED)

                new_window.destroy()  # 关闭窗口

        confirm_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='确认',
            style='own.TButton',
            command=on_confirm_clicked
        )
        confirm_button.place(x=140, y=70, height=25, width=80)
        cancel_button = ttk.Button(  # 注意是ttk的button
            new_window,
            text='取消',
            style='own.TButton',
            command=new_window.destroy  # 按钮按下，关闭窗口
        )
        cancel_button.place(x=230, y=70, height=25, width=80)

    def on_delete_word_fix_in_selected_word_fix_list(self, *args):
        # 删除当前列表中一个前后缀的信息
        complete_sentence = self.selected_word_fix_list_show_content.selection_get()  # 当前选中的前后缀
        word_fix = re.split(self.content_sample_entry.get(), complete_sentence, 1)
        for one_pair in self.selected_word_fix_list:  # 这里没有content sample
            if word_fix[0] == one_pair[0] and word_fix[1] == one_pair[1]:
                self.selected_word_fix_list.remove(one_pair)
                break
        # 更新listbox
        self.selected_word_fix_list_show_content.delete(0, tkinter.END)
        for one_word_fix in self.selected_word_fix_list:
            self.selected_word_fix_list_show_content.insert(
                tkinter.END,
                one_word_fix[0] + self.content_sample_entry.get() + one_word_fix[1])
        # 一些按钮失效
        self.copy_word_fix_to_lib_button.configure(state=tkinter.DISABLED)
        self.modify_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)
        self.delete_word_fix_in_selected_word_fix_list.configure(state=tkinter.DISABLED)

        self.up_button.configure(state=tkinter.DISABLED)
        self.down_button.configure(state=tkinter.DISABLED)
        self.up_to_top_button.configure(state=tkinter.DISABLED)
        self.down_to_bottom_button.configure(state=tkinter.DISABLED)

    def move_up_in_selected_word_fix_list(self, *args):
        # 能进到这里肯定不是第一项
        complete_sentence = self.selected_word_fix_list_show_content.selection_get()  # 当前选中的前后缀
        word_fix = re.split(self.content_sample_entry.get(), complete_sentence, 1)
        cur_index = 0  # 当前选中前后缀的索引
        for i in range(0, len(self.selected_word_fix_list)):  # 这里没有content sample
            if word_fix[0] == self.selected_word_fix_list[i][0] and word_fix[1] == self.selected_word_fix_list[i][1]:
                cur_index = i
                break
        # 交换
        temp = self.selected_word_fix_list[cur_index - 1]
        self.selected_word_fix_list[cur_index - 1] = self.selected_word_fix_list[cur_index]
        self.selected_word_fix_list[cur_index] = temp

        # 更新listbox
        self.selected_word_fix_list_show_content.delete(0, tkinter.END)
        for one_word_fix in self.selected_word_fix_list:
            self.selected_word_fix_list_show_content.insert(
                tkinter.END,
                one_word_fix[0] + self.content_sample_entry.get() + one_word_fix[1])

        self.selected_word_fix_list_show_content.select_set(cur_index - 1)  # 再选中原来那个
        self.on_word_fix_in_selected_list_selected(args)  # 手动触发一下,,,这个args可能不是很对应

    def up_to_top_in_selected_word_fix_list(self, *args):
        # 能进到这里肯定不是第一项
        complete_sentence = self.selected_word_fix_list_show_content.selection_get()  # 当前选中的前后缀
        word_fix = re.split(self.content_sample_entry.get(), complete_sentence, 1)
        cur_index = 0  # 当前选中前后缀的索引
        for i in range(0, len(self.selected_word_fix_list)):  # 这里没有content sample
            if word_fix[0] == self.selected_word_fix_list[i][0] and word_fix[1] == self.selected_word_fix_list[i][1]:
                cur_index = i
                break
        # 前移至顶部
        for i in range(cur_index, 0, -1):
            temp = self.selected_word_fix_list[i - 1]
            self.selected_word_fix_list[i - 1] = self.selected_word_fix_list[i]
            self.selected_word_fix_list[i] = temp

        # 更新listbox
        self.selected_word_fix_list_show_content.delete(0, tkinter.END)
        for one_word_fix in self.selected_word_fix_list:
            self.selected_word_fix_list_show_content.insert(
                tkinter.END,
                one_word_fix[0] + self.content_sample_entry.get() + one_word_fix[1])

        self.selected_word_fix_list_show_content.select_set(0)  # 再选中原来那个
        self.on_word_fix_in_selected_list_selected(args)  # 手动触发一下,,,这个args可能不是很对应

    def move_down_in_selected_word_fix_list(self, *args):
        # 能进到这里肯定不是最后一项
        complete_sentence = self.selected_word_fix_list_show_content.selection_get()  # 当前选中的前后缀
        word_fix = re.split(self.content_sample_entry.get(), complete_sentence, 1)
        cur_index = 0  # 当前选中前后缀的索引
        for i in range(0, len(self.selected_word_fix_list)):  # 这里没有content sample
            if word_fix[0] == self.selected_word_fix_list[i][0] and word_fix[1] == self.selected_word_fix_list[i][1]:
                cur_index = i
                break
        # 交换
        temp = self.selected_word_fix_list[cur_index + 1]
        self.selected_word_fix_list[cur_index + 1] = self.selected_word_fix_list[cur_index]
        self.selected_word_fix_list[cur_index] = temp

        # 更新listbox
        self.selected_word_fix_list_show_content.delete(0, tkinter.END)
        for one_word_fix in self.selected_word_fix_list:
            self.selected_word_fix_list_show_content.insert(
                tkinter.END,
                one_word_fix[0] + self.content_sample_entry.get() + one_word_fix[1])

        self.selected_word_fix_list_show_content.select_set(cur_index + 1)  # 再选中原来那个
        self.on_word_fix_in_selected_list_selected(args)  # 手动触发一下,,,这个args可能不是很对应

    def down_to_bottom_in_selected_word_fix_list(self, *args):
        # 能进到这里肯定不是最后一项
        complete_sentence = self.selected_word_fix_list_show_content.selection_get()  # 当前选中的前后缀
        word_fix = re.split(self.content_sample_entry.get(), complete_sentence, 1)
        cur_index = 0  # 当前选中前后缀的索引
        for i in range(0, len(self.selected_word_fix_list)):  # 这里没有content sample
            if word_fix[0] == self.selected_word_fix_list[i][0] and word_fix[1] == self.selected_word_fix_list[i][1]:
                cur_index = i
                break
        # 交换
        for i in range(cur_index, len(self.selected_word_fix_list) - 1):
            temp = self.selected_word_fix_list[i + 1]
            self.selected_word_fix_list[i + 1] = self.selected_word_fix_list[i]
            self.selected_word_fix_list[i] = temp

        # 更新listbox
        self.selected_word_fix_list_show_content.delete(0, tkinter.END)
        for one_word_fix in self.selected_word_fix_list:
            self.selected_word_fix_list_show_content.insert(
                tkinter.END,
                one_word_fix[0] + self.content_sample_entry.get() + one_word_fix[1])

        self.selected_word_fix_list_show_content.select_set(len(self.selected_word_fix_list) - 1)  # 再选中原来那个
        self.on_word_fix_in_selected_list_selected(args)  # 手动触发一下,,,这个args可能不是很对应


# 管理界面，登录时先启动这个界面，有个run，返回True或False，表示是否设置成功，成功了再启动MainInterface
class InterfaceManager():
    def __init__(self):
        self.dataManager = DataManager()
        self.liveRoomLib = self.dataManager.get_live_room_lib()
        self.wordFixLib = self.dataManager.get_word_fix_lib()
        # print(self.liveRoomLib)
        # print(self.wordFixLib)
        self.sending_list = []
        self.word_fix_list = []

        # 读完之后将两个库数据传给两个页面，Manager保存这两个页面
        self.root = tkinter.Tk()
        self.root.title('向多个直播间发送弹幕')
        width = 800
        height = 480
        to_left = (self.root.winfo_screenwidth() - width) / 2
        to_top = (self.root.winfo_screenheight() - height) / 2
        # 居中
        self.root.geometry("%dx%d+%d+%d" % (width, height, to_left, to_top))
        self.root.resizable(0, 0)  # 固定窗口大小
        self.page_list = []
        self.page_index = 0  # 当前是哪一页
        self.create_widgets()
        self.show_page(0)
        self.root.mainloop()

    def create_widgets(self):
        self.page_list.append(LiverRoomSettingFrame(self.root, self, self.liveRoomLib))
        self.page_list.append(WordFixSettingPage(self.root, self, self.wordFixLib))
        for page in self.page_list:
            page.place(x=0, y=0)

    def show_page(self, page_index):
        self.page_list[page_index].tkraise()

    def goto_next_page(self):
        # 能到这里肯定是有下一页的
        self.page_index += 1
        self.show_page(self.page_index)

    def goto_previous_page(self):
        # 能到这里肯定是有上一页的
        self.page_index -= 1
        self.show_page(self.page_index)

    def restart_setting_page(self):
        # 重新显示设置界面
        self.root.update()
        self.root.deiconify()
        self.page_index = 0
        self.show_page(0)

    def finish(self):
        # 设定完毕
        live_room_lib = self.page_list[0].get_live_room_lib()  # 也可以直接用self.liveRoomLib
        sending_list = self.page_list[0].get_sending_list()

        word_fix_lib = self.page_list[1].get_word_fix_lib()  # 也可以直接用self.wordFixLib
        word_fix_list = self.page_list[1].get_word_fix_list()
        content_sample = self.page_list[1].get_content_sample()
        # 进行一些判断
        if len(sending_list) == 0:
            tkinter.messagebox.showwarning(
                title='提示',
                message='发送房间列表为空',
                parent=self.root  # 这样才会显示在当前窗口上方
            )
            self.page_index = 0
            self.show_page(0)
        elif len(word_fix_list) != 0 and len(content_sample) == 0:
            tkinter.messagebox.showwarning(
                title='提示',
                message='在使用前后缀时，示例不能为空',
                parent=self.root  # 这样才会显示在当前窗口上方
            )
            self.page_index = 1
            self.show_page(1)
        else:
            self.dataManager.save_live_room_lib(live_room_lib)
            self.dataManager.save_word_fix_lib(word_fix_lib)
            self.root.withdraw()  # 这里不关闭而是隐藏
            # 传递参数
            room_id_list = []
            for room in sending_list:
                room_id_list.append(room[1])  # 把房间号存下来
            MainInterface(self, room_id_list, content_sample, word_fix_list).run()

    def stop(self):
        # 真正的关闭窗口
        self.root.destroy()

# if __name__ == "__main__":
#     ManagerInterface()

