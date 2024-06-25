from AT_Platform.templates import template
from AT_Platform.function import common
from AT_Platform.function.platform import platform
from AT_Platform.function.sport import sport
import reflex as rx


class BetState(rx.State):
    processing_hidden = False
    env_list : list[str] = ["pre-prod","qa1"]
    vend_list : list[str] = ["pp001","vd001"]
    currency_list: list[str] = ["CNY"]
    all_env : dict
    selected_env : str
    selected_vend : str
    selected_curreny : str
    sid : str
    inplay : str   
    cashout : str
    table_hidden = True 
    table_data: list[list[str]] = []
    columns: list[str] = ["順序","投注時間","賽事代號","盤口代號","投注項","K值","賠率","注單號","投注結果"]
    bet_info: str
    fail_log: str

    async def get_env(self):
        env = common.get_env_data()
        self.all_env = dict(env)
        self.env_list = list(self.all_env.keys())
        self.processing_hidden = True

    def get_vend(self,value):
        if value : 
            self.selected_env = value
            self.vend_list = list(self.all_env[value].keys())

    def get_currency(self,value):
        self.selected_vend = value
        self.currency_list = common.get_currency(
            self.all_env[self.selected_env][self.selected_vend]['api_url'],
            self.all_env[self.selected_env][self.selected_vend]['platform_url']
        )

    def bet(self, form_data: dict):
        self.processing_hidden = False  
        form_data['env'] = self.selected_env             
        form_data['sid'] = self.sid
        form_data['inplay'] = self.inplay == "Y"
        form_data['currency'] = self.selected_curreny
        form_data['api_url'] = self.all_env[self.selected_env][self.selected_vend]['api_url']
        form_data['platform_url'] = self.all_env[self.selected_env][self.selected_vend]['platform_url']
        return BetState.send_bet(form_data)

    def isfloat(self,num):
        try:
            float(num)
            return True
        except ValueError:
            return False
    
    @rx.background
    async def send_bet(self, bet_data:dict):        
        async with self:      
            self.table_data = []                  
            platform_user = platform(bet_data['api_url'],bet_data['platform_url'])
            if platform_user.platform_login(bet_data['account'],bet_data['password']) :
                amount = platform_user.getwallet(bet_data['currency'])
                stoken = platform_user.sport_login()
                if stoken != None :
                    sport_user = sport(self.selected_env,bet_data['api_url'],bet_data['platform_url'],stoken)
                    self.table_data, pass_count, fail_count, fail_msg = sport_user.bet_process(bet_data)
                    amount2 = platform_user.getwallet(bet_data['currency'])
                    self.bet_info = f"投注前餘額: {amount} , 投注後餘額: {amount2}, \n 共投注 {pass_count+fail_count} 注, 成功 {pass_count} 注"
                    self.fail_log = fail_msg
                    if self.cashout == "Y":
                        if "提前結算金額" not in self.columns :
                            self.columns.append("提前結算金額")
                        count=0
                        for data in self.table_data:
                            if data[8] == 'OK':
                                amount = sport_user.chashout(data[7])
                                data.append(amount)
                                try:
                                    if int(amount) >= int(bet_data['ante']) :
                                        count +=1
                                except :
                                    pass
                        self.fail_log += f"提前結算金額大於本金{bet_data['ante']}的有{count}筆"
                                
                else :
                    self.fail_log  = "sport login failed"
            else :
                self.fail_log = "platform login failed"

            self.processing_hidden = True 
            self.table_hidden = False


@template(route="/bet", title="賽事投注", on_load=BetState.get_env)
def single_bet() -> rx.Component:

    return rx.vstack(
        rx.heading("賽事投注", size="6"),
        rx.image(src="/loading.gif",height="5em",hidden=BetState.processing_hidden),
        rx.form(
            rx.chakra.hstack(
                rx.text("選擇環境: "),
                rx.select(                
                    BetState.env_list,
                    on_change=lambda value: BetState.get_vend(value),
                ),    
                rx.text(" 選擇業主: "),
                rx.select(                
                    BetState.vend_list,
                    on_change=lambda value: BetState.get_currency(value),
                ),
                rx.text(" 選擇幣種: "),
                rx.select(                
                    BetState.currency_list,
                    value=BetState.selected_curreny,
                    on_change=BetState.set_selected_curreny,
                ),                
            ),
            rx.chakra.hstack(
                rx.text("帳號 :"),
                rx.input(id="account"),
                rx.text(" 密碼 :"),
                rx.input(id="password"),
            ),  
            rx.chakra.hstack(  
                rx.text("選擇球種: "),
                rx.radio(["1","2","3","4"], direction="row", spacing="1",
                            on_change=BetState.set_sid),
                rx.spacer(spacing='1'),
                rx.text("滾球: "),
                rx.radio(["Y","N"], direction="row", spacing="1",
                            on_change=BetState.set_inplay),
                rx.spacer(spacing='1'),
                rx.text("是否提前結算: "),
                rx.radio(["Y","N"], direction="row", spacing="1",
                            on_change=BetState.set_cashout),
            ),
            rx.chakra.hstack(
                rx.text("賽事iid:"),
                rx.input(id="iid",placeholder="多iid中間請加上 ;"),
                rx.spacer(spacing='1'),
                rx.text("盤口代碼:"),
                rx.input(id="market",placeholder="可用 ; 區隔"),
                rx.spacer(spacing='1'),
                rx.text("投注金額:"),
                rx.input(id="ante",placeholder=""),
            ),  
            rx.button("送出",type="submit"),
            on_submit=BetState.bet,
            reset_on_submit=False, 
        ),
        rx.vstack(
            rx.divider(),
            rx.text(BetState.bet_info),
            rx.text(BetState.fail_log),
            rx.spacer(), 
            rx.data_table(
                columns=BetState.columns,
                data=BetState.table_data,
                row_height=50,
                column_select="single",
            ),hidden=BetState.table_hidden
        )
    )