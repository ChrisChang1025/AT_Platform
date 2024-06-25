from AT_Platform.templates import template

import reflex as rx
from Crypto.Cipher import AES
import base64
import time

KEY_ONE = bytes("3t6w9z$C&F)J@NcRfUjWnZr4u7x!A%D*", 'utf-8')
KEY_TWO = bytes("u8x/A?D*G-KaPdSgVkYp3s6v9y$B&E)H", 'utf-8')
KEY_THREE = bytes("Zr4u7x!A%D*F-JaNdRgUkXp2s5v8y/B?", 'utf-8')

class DecryptState(rx.State):
    form_data: str
    hidden = True
    processing_hidden = True
        
    def decrypt(self, form_data: dict):
        self.form_data = self.decrypt_act(form_data['phone1'],form_data['phone2'],form_data['phone3'])
        self.hidden = False
    
    def decrypt_act(self,phone1,phone2,phone3):
        cipher = AES.new(KEY_ONE, AES.MODE_ECB)
        _phone1 = cipher.decrypt(base64.b64decode(phone1)).decode('utf-8').strip()
        cipher = AES.new(KEY_TWO, AES.MODE_ECB)
        _phone2 = cipher.decrypt(base64.b64decode(phone2)).decode('utf-8').strip()
        cipher = AES.new(KEY_THREE, AES.MODE_ECB)
        _phone3 = cipher.decrypt(base64.b64decode(phone3)).decode('utf-8').strip()
        return self.convert_to_html_entities(_phone1 + _phone2 + _phone3)
    
    def convert_to_html_entities(self,text):
        html_entities = []
        for char in text:
            if char.isdigit():
                html_entities.append(char)
        return ''.join(html_entities)
    
    async def upload(self,files: list[rx.UploadFile]):
        result = list()
        self.processing_hidden = False
        for file in files:
            content = await file.read()
            lines = content.decode('utf-8').split("\n")[1:]
            for line in lines:
                args = line.split(',')
                result.append(args[0]+','+self.decrypt_act(args[1],args[2],args[3]))

        self.processing_hidden = True
        return rx.download(
            data="\n".join(result),
            filename="result.csv")
        

@template(route="/decrypt", title="查詢會員電話")
def decrypt_number() -> rx.Component:

    return rx.vstack(
        rx.heading("解密電話號碼", size="6"),
        rx.form(
            rx.vstack(
                rx.chakra.hstack(
                    rx.text("phone1 :"),
                    rx.input(id="phone1"),
                ),
                rx.chakra.hstack(
                    rx.text("phone2 :"),
                    rx.input(id="phone2"),
                ),
                rx.chakra.hstack(
                    rx.text("phone3 :"),
                    rx.input(id="phone3"),
                ),        
                rx.button("送出",type="submit"),
                rx.text(DecryptState.form_data.to_string(),hidden=DecryptState.hidden)
            ),
            on_submit=DecryptState.decrypt,
            reset_on_submit=False,            
        ),
        rx.divider(),
        rx.chakra.hstack(
            rx.upload(rx.button("選擇檔案"),id='upload1',max_files=1),
            rx.button("上傳",
                      on_click=DecryptState.upload(rx.upload_files(upload_id="upload1")),
                      ),
            rx.link("範例下載", href="/getPhoneNumber上傳檔案.csv"),
        ),             
        rx.image(src="/loading.gif",height="5em",hidden=DecryptState.processing_hidden)
    )