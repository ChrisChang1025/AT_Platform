import asyncio
import json
from collections import Counter
from AT_Platform.templates import template
from AT_Platform.function import common
from AT_Platform.function import lottery
import reflex as rx
from threading import Thread


class LotteryWithdraw(rx.State):
    processing_hidden = False
    openBtn_hidden = True
    loginBtn_hidden = False
    data_hidden = True
    lott_dict: dict
    data_column = [
        {
            "title": "checkbox",
            "type": "bool"
        },
        {
            "title": "notice",
            "type": "str"
        },
        {
            "title": "vendorName",
            "type": "str"
        },
        {
            "title": "round",
            "type": "str"
        },
        {
            "title": "openNum",
            "type": "str"
        },
        {
            "title": "result",
            "type": "str"
        }
    ]
    withdrawNum_data: list
    doOpen_result: dict

    def get_allUrls(self):
        with open('./assets/lotteryUrl.json') as f:
            self.lott_dict = json.load(f)['prod']
        self.processing_hidden = True
        self.lott_allKeys = list(self.lott_dict.keys())

    async def doLogin_admin(self, form_data: dict):
        self.data_hidden = True
        self.processing_hidden = False
        self.loginBtn_hidden = True
        yield
        thread_list = []
        result_list = []
        for vendName in list(self.lott_dict):
            t = ThreadWithReturnValue(target=lottery.doFirst_step, args=(vendName, self.lott_dict, form_data))
            thread_list.append(t)
            t.start()

        for i in thread_list:
            result_list.append({'vendName': i._args[0], 'result': i.join()})

        # print("=================================================")
        # print(result_list)
        result_list
        for res in result_list:
            if result_list is not None:
                self.lott_dict[res['vendName']].update(res['result'])

        openNum_list = []
        for vendName in list(self.lott_dict):
            myObj = self.lott_dict[vendName]
            if myObj['openNum'] != '' or myObj['openNum'] != None:
                openNum_list.append(myObj['openNum'])

        if len(openNum_list) == 0:
            print("no data")
        else:
            uq_counter = Counter(openNum_list)
            maxCount = max(uq_counter, key=uq_counter.get)
            set_oepn = True
            self.withdrawNum_data = []
            for vendName in list(self.lott_dict):
                myObj = self.lott_dict[vendName]
                if myObj['openNum'] != 'No record' and myObj['openNum'] == maxCount:
                    self.withdrawNum_data.append([True, myObj['errorMsg'], vendName, str(myObj['round']), str(myObj['openNum']), ''])
                    set_oepn = False
                elif myObj['openNum'] != 'No record':
                    self.withdrawNum_data.append([False, myObj['errorMsg'] + '!!開獎號碼有誤', vendName, str(myObj['round']), str(myObj['openNum']), ''])
                    set_oepn = False
                else:
                    self.withdrawNum_data.append([False, myObj['errorMsg'], vendName, str(myObj['round']), str(myObj['openNum']), ''])

            self.openBtn_hidden = set_oepn
            self.data_hidden = False
            self.processing_hidden = True
            self.loginBtn_hidden = False

    async def doOpen(self):
        self.loginBtn_hidden = True
        self.openBtn_hidden = True
        self.processing_hidden = False
        yield
        thread_list = []
        result_list = []
        for idx, data_list in enumerate(self.withdrawNum_data):
            if data_list[0] == True:
                # print(data_list)
                keyName = data_list[2]
                # print(f"keyName = {keyName}")
                # print(self.lott_dict[keyName])
                t = ThreadWithReturnValue(target=lottery.do_openLottery, args=(keyName, self.lott_dict, idx))
                thread_list.append(t)
                t.start()
                # self.doOpen_result[keyName] = lottery.do_openLottery(keyName, self.lott_dict)
                # self.withdrawNum_data[idx][5] = self.doOpen_result[keyName]

        await asyncio.sleep(4)
        for i in thread_list:
            result_list.append({'keyName': i._args[0], 'index': i._args[2], 'result': i.join()})

        # print("=================================================")
        # print(result_list)
        await asyncio.sleep(2)
        result_list
        for res in result_list:
            if result_list is not None:
                self.withdrawNum_data[res['index']][5] = res['result']
        self.processing_hidden = True
        self.openBtn_hidden = True
        self.loginBtn_hidden = False

    def get_clicked_data(self, data) -> bool:
        if data[0] == 0:
            if self.withdrawNum_data[data[1]][0] == True:
                self.withdrawNum_data[data[1]][0] = False
            else:
                self.withdrawNum_data[data[1]][0] = True


@template(route="/lottery", title="彩票後台結算", on_load=LotteryWithdraw.get_allUrls)
def lottery_withdraw() -> rx.Component:

    return rx.vstack(
        rx.heading("彩票後台結算", size="6"),
        rx.image(src="/loading.gif", height="5em", hidden=LotteryWithdraw.processing_hidden),
        rx.form(
            rx.vstack(
                rx.chakra.hstack(
                    rx.text("帳號 :"),
                    rx.input(id="account"),
                    rx.text("密碼 :"),
                    rx.input(id="password"),
                    rx.button("登入", type="submit", hidden=LotteryWithdraw.loginBtn_hidden)
                )
            ),
            on_submit=LotteryWithdraw.doLogin_admin,
            reset_on_submit=False,
        ),
        rx.vstack(
            rx. divider(),
            rx.data_editor(
                data=LotteryWithdraw.withdrawNum_data,
                columns=LotteryWithdraw.data_column,
                on_cell_clicked=LotteryWithdraw.get_clicked_data
            ),
            rx.chakra.hstack(
                rx.button("結算", on_click=LotteryWithdraw.doOpen, hidden=LotteryWithdraw.openBtn_hidden),
            ),
            hidden=LotteryWithdraw.data_hidden
        )
    )


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
        Thread.__init__(self, group, target, name, args, kwargs, daemon=daemon)

        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self):
        Thread.join(self)
        return self._return
