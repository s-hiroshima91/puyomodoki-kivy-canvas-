import kivy
import math
import numpy as np
import random

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.graphics import Line
from kivy.graphics import Ellipse
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.properties import ListProperty
from kivy.core.window import Window


class GameWindowWidget(Widget):
    score = StringProperty('')

    def __init__(self, **kwargs):
        super(GameWindowWidget, self).__init__(**kwargs)
        self.score = '0'

class BoardWidget(Widget):
    def __init__(self, **kwargs):
        super(BoardWidget, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        
    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'left':
            judge = -1
        elif keycode[1] == 'right':
            judge = 1
        elif keycode[1] == 'z':
            judge = 2
        elif keycode[1] == 'x':
            judge = -2
        elif keycode[1] == 'down':
            judge = 3
        else:
            judge = 0

        if ((judge != 0)&(DM.refuse_flag != 1)):
            DM.cdw.move_func(judge)

        return True
    
class HelpPopup(Popup):
    pass

class GameOverPopup(Popup):
    pass

def rot_matrix(d, pos1, pos2):
    vect_1 = np.array(pos1)
    vect_2 = np.array(pos2)
    vect = np.subtract(vect_2, vect_1)
    A = np.array([[math.cos(d), - math.sin(d)], [math.sin(d), math.cos(d)]])
    vect = A @ vect
    vect = np.add(vect_1, vect)
    return vect.tolist()

def key_judge_func(x, y):
    
    if ((150 <= x <= 250) & (250 <= y <= 350)):
        judge = -1
    elif ((350 <= x <= 450) & (250 <= y <= 350)):
        judge = 1
    elif ((250 <= x <= 350) & (150 <= y <= 250)):
        judge = 3
    elif ((650 <= x <= 750) & (250 <= y <= 350)):
        judge = 2
    elif ((800 <= x <= 900) & (200 <= y <= 300)):
        judge = -2
    else:
        judge = 0
        
    return judge

def color_convert(num):
    bin_num = int(bin(num), 0)
    color_rgb =[0, 0, 0]
    for i in range(3):
        color_rgb[i] = (bin_num >> i) & 0b1
    return color_rgb

def convert_pos(pos):
        temp = [240, 400]
        for i in range(2):
            temp[i] = int((pos[i] - temp[i]) / 100) 

        return temp

def collision_detect(move_x, move_y, pos):        
        return DM.stack_manage[pos[0] + 1 + move_x][pos[1] + 1 + move_y]

def freefall(x):
    l_1d = DM.stack_manage[x][:]
    len1 = l_1d.size
    l_1d = l_1d[l_1d != 0]
    len2 = l_1d.size
    temp = np.zeros(len1 - len2 , dtype = int)
    l_1d = np.append(l_1d, temp)
    DM.stack_manage[x][:] = l_1d
    return len2

#繋がっているドロップをグループ分けする関数
def group_func(Matrix):
    #C言語の2重ポインタみたいやり方で分ける。
    #pythonはポインタがないので強引にやる。
    offset = 10 #アドレスを指定している場合は10から始まることとして区別する
    pointer = np.array([], dtype = int) 
    parameter = np.array([], dtype = int)
    #左下のドロップから走査する
    for i in range(6):
        j = 1
        while ((0 < Matrix[i + 1][j]) & (j <= 14)):
            color = Matrix[i + 1][j] #よく使うので短い変数名にしておく
            if (0 < color < 7): #ドロップがあることとと未チェックであることの確認
                len = parameter.size #パラメータのアドレスを取得
                addr = pointer.size #ポインタのアドレスを取得
                pointer = np.append(pointer, len) #ポインタにパラメータのアドレスを記録
                parameter = np.append(parameter, [color, 1]) #パラメータに色と数を記録
#                len2 = pointer.size
#                addr = len2 + offset
                Matrix[i + 1][j] = addr + offset #ポインタのアドレスをもとのデータに記録

            elif (offset <= color): #すでにチェック済みの場合
                addr = color - offset #参照するアドレスを取得
                color = parameter[pointer[addr]] #色の番号を取得

            for k in range(2): #上と右のドロップを確認
                num = Matrix[i + 1 + k][j + 1 - k ]
                if (num == color):
                    parameter[pointer[addr] + 1] += 1 #ドロップの数を追加
                    Matrix[i + 1 + k][j + 1 - k] = addr + offset #ポインタのアドレスをもとのデータに記録
                elif (offset <= num):
                    addr2 = num - offset
                    color2 = parameter[pointer[addr2]]
                    if ((color2 == color) & (pointer[addr2] != pointer[addr])): #参照先は違うが色が同じ場合、同じグループにまとめる
                        parameter[pointer[addr] + 1] += parameter[pointer[addr2] + 1] #数を合計する
                        pointer[addr2] = pointer[addr] #ポインタの参照先を同じにする

            j += 1

    len = parameter.size
    score = 0
    for i in range(int(len / 2)): # 4個以上たまったドロップを削除
        if (parameter[2 * i + 1] >= 4):
            score += parameter[2 * i + 1]
            parameter[2 * i] = 0

    for i in range(6): #ドロップのスタック情報を更新
        j = 1
        while((offset <= Matrix[i+1][j]) & (j <= 15)):
            Matrix[i+1][j] = parameter[pointer[Matrix[i+1][j] - offset]]
            j += 1

    return score


class DropManage():
    def __init__(self):
        l_2d = [[9] * 15 for i in range(8)]
        self.name = [['null'] * 12 for i in range(6)]
        for i in range(6):
            l_2d[i+1][1 : 15] = [0]*14

        self.stack_manage = np.array(l_2d)
        for i in range(6):
            for j in range(12):
                self.name[i][j] = 'stack' + str(i) +'_' + str(j)

        self.drop_color = [[0, 0],[0, 0]]

        for i in range(2):
            for j in range(2):
                self.drop_color[i][j] = random.randrange(1, 6, 1)
            
        self.refuse_flag = 1
        self.cdw = 'cdw'

DM = DropManage()

class CurrentDropWidget(Widget):
    master_pos = ListProperty([440, 1500])
    slave_pos = ListProperty([440, 1400])
    MasterColor = ListProperty([0, 0, 0])
    SlaveColor = ListProperty([0, 0, 0])
 
    def __init__(self, next_drop, **kwargs):
        super(CurrentDropWidget, self).__init__(**kwargs)

        self.nd = next_drop
        if (self.nd == 1):
            self.master_pos = [880, 1320]
            self.slave_pos = [880, 1220]
        self.test()

    def test(self):
        self.count = 0
        self.MasterColor = color_convert(DM.drop_color[0][self.nd])
        self.SlaveColor = color_convert(DM.drop_color[1][self.nd])

    def on_touch_down(self, touch):
        if (self.nd == 0):
            x = touch.pos[0]
            y = touch.pos[1]
            judge = key_judge_func(x, y)
            if (judge != 0):
                self.move_func(judge)

    def move_func(self, judge):
        if (DM.refuse_flag == 0):
            pos= []        
            pos1 = convert_pos(self.master_pos)
            pos2 = convert_pos(self.slave_pos)
            pos = [pos1, pos2]

            flag = 0
            if (abs(judge) == 1):
                for i in range(2):
                    flag += collision_detect(judge, 0, pos[i])

                if (flag == 0):
                    self.master_pos[0] = self.master_pos[0] + judge * 100
                    self.slave_pos[0] = self.slave_pos[0] + judge * 100

            elif (abs(judge) == 2): 
                temp_pos = rot_matrix(math.pi / judge, self.master_pos, self.slave_pos)  
                pos = convert_pos(temp_pos)
                flag += collision_detect(0, 0, pos)
                if (flag == 0):
                    self.slave_pos = temp_pos
                else:
                    temp_pos = rot_matrix(math.pi, self.master_pos, temp_pos)  
                    pos = convert_pos(temp_pos)
                    flag *= collision_detect(0, 0, pos)
                    if (flag == 0):
                        self.slave_pos = self.master_pos
                        self.master_pos = temp_pos

            elif (judge == 3):
                for i in range(2):
                    flag += collision_detect(0, -1, pos[i])
                if (flag == 0):
                    self.master_pos[1] -= 100
                    self.slave_pos[1] -= 100

class StackDropWidget(Widget):
    StackColor = ListProperty([0, 1, 0])
    StackPosition = ListProperty([440, 1500])
    def __init__(self, i, j, **kwargs):
        super(StackDropWidget, self).__init__(**kwargs)
        self.I = i
        self.J = j
        self.count = 0
        self.StackPosition = [self.I * 100 + 240 , self.J * 100 + 400 ]
        self.drow_color()

    def drow_color(self):
        self.StackColor = color_convert(DM.stack_manage[self.I + 1][self.J + 1])

def ini_Pop(dt):
    HelpPopup().open()
    
def GOPop():
    GameOverPopup().open()

class PuyopuyoApp(App):

    def start_func(self):
        DM.refuse_flag = 0
        DM.cdw = CurrentDropWidget(0)
        self.root.add_widget(DM.cdw)
        self.ndw = CurrentDropWidget(1)
        self.root.add_widget(self.ndw)
        Clock.schedule_once(self.fall_func, 0.95)
        
    def board_func(self):
        BW = BoardWidget()

    def ini_drow(self):
        root = FloatLayout(size = (1080, 1920))
        self.gww = GameWindowWidget()
        root.add_widget(self.gww)
        

        for i in range(6):
            for j in range(12):
                DM.name[i][j] = StackDropWidget(i, j)
                root.add_widget(DM.name[i][j])
        Clock.schedule_once(ini_Pop, 1)

        return root

    def fall_func(self, dt):
        pos= []        
        pos1 = convert_pos(DM.cdw.master_pos)
        pos2 = convert_pos(DM.cdw.slave_pos)
        pos = [pos1, pos2]

        flag = 0
        for i in range(2):
            flag += collision_detect(0, -1, pos[i])

        if (flag == 0):
            DM.cdw.master_pos[1] -= 100
            DM.cdw.slave_pos[1] -= 100
            Clock.schedule_once(self.fall_func, 0.95)
        
        else:
            DM.refuse_flag = 1
            for i in range(2):
                DM.stack_manage[pos[i][0] + 1][pos[i][1] + 1] = DM.drop_color[i][0]

            DM.cdw.master_pos = [2000, 3000]
            DM.cdw.slave_pos = [2000, 3000]
                 
            for i in range(2):
                if (pos[0][0] == pos[1][0]):
                    len = pos[i][1] + 2
                else:
                    len = freefall(pos[i][0] + 1)

                DM.name[pos[i][0]][len - 2].drow_color()
                DM.drop_color[i][0] = DM.drop_color[i][1]
                DM.drop_color[i][1] = random.randrange(1, 6, 1)

            self.count = 0
            Clock.schedule_once(self.erase_func, 0)

    def erase_func(self, dt):
        increase_score = group_func(DM.stack_manage)
        self.count += 1
        now_score = int(self.gww.score)
        self.gww.score = str(now_score + self.count *increase_score)

        for i in range(6):
                
            len = freefall(i + 1)
            for j in range(12):               
                DM.name[i][j].drow_color()

        if (increase_score > 0):
            Clock.schedule_once(self.erase_func, 1)
        else:
            DM.refuse_flag = 0
            self.next_func()

    def next_func(self):

        DM.cdw.master_pos = [440, 1500]
        DM.cdw.slave_pos = [440, 1400]
        pos = convert_pos(DM.cdw.slave_pos)

        flag = 0
        flag += collision_detect(0, 0, pos)

        if (flag != 0):
            GOPop()
        else:
            DM.cdw.MasterColor = color_convert(DM.drop_color[0][0])
            DM.cdw.SlaveColor = color_convert(DM.drop_color[1][0])
            self.ndw.MasterColor = color_convert(DM.drop_color[0][1])
            self.ndw.SlaveColor = color_convert(DM.drop_color[1][1])
            Clock.schedule_once(self.fall_func, 0.95)

    def build(self):
        return self.ini_drow()

if __name__ == '__main__':
    PuyopuyoApp().run()