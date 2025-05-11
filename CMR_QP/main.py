from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

class MainLayout(BoxLayout):

    def on_textinput_weight(self, text):
        try:
            if text == 'C':
                self.ids.wt.value  = ''
                return
            if self.ids.wt.value == '0':
                self.ids.wt.value = text
                return

            self.ids.wt.value += text
            value = float(self.ids.wt.value)

            if value > 200:
                self.ids.wt.value = text
                return
            value = value * 0.15
            aif = round(max(value / 21, 0.5), 1)
            self.ids.aif.value = str(aif)
            rest1 = round((value - aif) / 2, 1)
            rest2 = round(value - aif - rest1, 1)
            self.ids.rest1.value = str(max(rest1, rest2))
            self.ids.rest2.value = str(min(rest1, rest2))
            self.ids.qp.value = str(round(aif + max(rest1, rest2), 1))
        except ValueError:
            pass

class MainApp(App):
    def build(self):
        self.ml = MainLayout()
        return self.ml

MainApp().run()