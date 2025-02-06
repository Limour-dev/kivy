from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

from contextlib import redirect_stdout
from io import StringIO
import traceback

from kivy.uix.popup import Popup
from kivy.clock import Clock
import asyncio
from threading import Thread, Event
import inspect

class AsyncRun:

    def event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        self.loop.close()

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.ep = Thread(target=self.event_loop, daemon=True)
        self.ep.start()

    def __call__(self, intervals, callback, *args):
        task = self.try_call(callback, args)
        if intervals <= 0:
            self.run(task)
            return
        self.loop.call_later(intervals, self.run, task)

    def run(self, task):
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def try_call(self, callback, args):
        try:
            task = callback(*args)
            if inspect.iscoroutine(task):
                self.run(task)
        except Exception as e:
            print(e)

class REPL:
    def __init__(self, update_text):
        self.asyncrun = AsyncRun()
        self.globals = {
            'print': self.output,
            'input': self.input,
            'asyncrun': self.asyncrun,
            'ui_run': Clock.schedule_once
        }
        self.history = []
        self.update_text = update_text
        self.popup_event = Event()

    def input(self, _prompt=''):

        input_text = ''

        def ui_popup(dt):
            nonlocal input_text

            def on_confirm(instance):
                popup.dismiss()
                nonlocal input_text
                input_text = text_input.text
                self.popup_event.set()

            content = BoxLayout(orientation='vertical')
            text_input = TextInput(multiline=True, hint_text=str(_prompt))
            confirm_button = Button(text='确认', size_hint=(1, 0.3))
            confirm_button.bind(on_press=on_confirm)

            content.add_widget(text_input)
            content.add_widget(confirm_button)

            popup = Popup(
                title='请输入',
                content=content,
                size_hint=(0.8, 0.3)
            )

            popup.open()

        Clock.schedule_once(ui_popup)
        self.popup_event.wait()
        self.popup_event.clear()

        self.output(input_text)
        return input_text

    def output(self, *args, **kwargs):
        with StringIO() as output:
            with redirect_stdout(output):
                print(*args, **kwargs)
            output_text = output.getvalue()
            output_text = output_text.replace('\u00a0', '')
            self.history.append(output_text)
        self.ui_update()

    def ui_update(self):
        Clock.schedule_once(lambda dt: self.update_text('\n'.join(self.history)))

    def asyncExec(self, code: str):
        try:
            self.history.append(f'>>> {code}')
            self.ui_update()
            try:
                res = eval(code, self.globals)
                if res is not None:
                    self.output(res)
                return
            except SyntaxError:
                pass
            exec(code, self.globals)
        except Exception:
            self.output(traceback.format_exc())

    def exec(self, code: str):
        self.asyncrun(0, self.asyncExec, code)


class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 设置布局为垂直方向
        self.orientation = 'vertical'

        # 创建输入文本框
        self.input_text = TextInput(
            multiline=True,  # 允许多行输入
            size_hint=(1, 4),  # 设置高度占比
            hint_text='>>>'  # 提示文字
        )

        self.buttons = BoxLayout(orientation='horizontal')
        self.buttons_build()

        # 创建输出文本框
        self.output_text = TextInput(
            multiline=True,  # 允许多行
            size_hint=(1, 4),  # 设置高度占比
        )

        # 将控件添加到布局中
        self.add_widget(self.input_text)
        self.add_widget(self.buttons)
        self.add_widget(self.output_text)

        self.repl = REPL(self.update_text)

    def buttons_build(self):

        def clear_input(instance):
            self.input_text.text = ''

        self.buttons.add_widget(
            Button(
                text='清空\n输入',
                size_hint=(1, 1),  # 设置高度占比
                on_press= clear_input # 绑定按钮点击事件
            )
        )

        def clear_output(instance):
            self.repl.history = []
            self.repl.ui_update()

        self.buttons.add_widget(
            Button(
                text='清空\n输出',
                size_hint=(1, 1),  # 设置高度占比
                on_press= clear_output # 绑定按钮点击事件
            )
        )

        def show_vars(instance):
            self.repl.output(self.repl.globals)

        self.buttons.add_widget(
            Button(
                text='查看\n变量',
                size_hint=(1, 1),  # 设置高度占比
                on_press= show_vars # 绑定按钮点击事件
            )
        )

        self.buttons.add_widget(
            Button(
                text='运行\n代码',
                size_hint=(1, 1),  # 设置高度占比
                on_press=self.exec  # 绑定按钮点击事件
            )
        )

    def exec(self, instance):
        input_text:str = self.input_text.text
        input_text = input_text.replace('\u00a0', '')
        self.repl.exec(input_text)

    def update_text(self, text):
        self.output_text.text = text

class MyApp(App):
    def build(self):
        return MainLayout()

MyApp().run()