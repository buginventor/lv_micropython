import usys as sys

sys.path.append('')  # See: https://github.com/micropython/micropython/issues/6419


# See: https://pymotw.com/2/sys/tracing.html

def mp_trace(frame, event, arg):
    co = frame.f_code
    func_name = co.co_name
    func_line_no = frame.f_lineno
    func_filename = co.co_filename
    print('[%s] [%s] %s:%s' % (event, func_name, func_filename, func_line_no))
    return mp_trace


# sys.settrace(mp_trace)

import lvgl as lv
from lv_utils import event_loop

# lvgl must be initialized before any lvgl function is called or object/struct is constructed!

lv.init()


##############################################################################
# Styles
##############################################################################

class ColorStyle(lv.style_t):
    def __init__(self, color):
        super().__init__()
        self.set_bg_opa(lv.OPA.COVER)
        self.set_bg_color(lv.color_hex3(color))
        self.set_bg_grad_color(lv.color_hex3(0xFFF))
        self.set_bg_grad_dir(lv.GRAD_DIR.VER)
        self.set_bg_main_stop(0)
        self.set_bg_grad_stop(128)


class ShadowStyle(lv.style_t):
    def __init__(self):
        super().__init__()
        self.set_shadow_opa(lv.OPA.COVER)
        self.set_shadow_width(3)
        self.set_shadow_color(lv.color_hex3(0xAAA))
        self.set_shadow_ofs_x(5)
        self.set_shadow_ofs_y(3)
        self.set_shadow_spread(0)


# A square button with a shadow when not pressed
class ButtonStyle(lv.style_t):
    def __init__(self):
        super().__init__()
        self.set_radius(lv.dpx(8))
        self.set_shadow_opa(lv.OPA.COVER)
        self.set_shadow_width(lv.dpx(10))
        self.set_shadow_color(lv.color_hex3(0xAAA))
        self.set_shadow_ofs_x(lv.dpx(10))
        self.set_shadow_ofs_y(lv.dpx(10))
        self.set_shadow_spread(0)


class ButtonPressedStyle(lv.style_t):
    def __init__(self):
        super().__init__()
        self.set_shadow_ofs_x(lv.dpx(0))
        self.set_shadow_ofs_y(lv.dpx(0))


##############################################################################
# Themes
##############################################################################

class AdvancedDemoTheme(lv.theme_t):

    def __init__(self):
        super().__init__()
        self.button_style = ButtonStyle()
        self.button_pressed_style = ButtonPressedStyle()

        # This theme is based on active theme (material)
        base_theme = lv.theme_get_from_obj(lv.scr_act())

        # This theme will be applied only after base theme is applied
        self.set_parent(base_theme)

        # Set the "apply" callback of this theme to our custom callback
        self.set_apply_cb(self.apply)

        # Activate this theme on default display
        lv.disp_get_default().set_theme(self)

    def apply(self, theme, obj):
        if obj.get_class() == lv.btn_class:
            obj.add_style(self.button_style, lv.PART.MAIN)
            obj.add_style(self.button_pressed_style, lv.PART.MAIN | lv.STATE.PRESSED)


##############################################################################

member_name_cache = {}


def get_member_name(obj, value):
    try:
        return member_name_cache[id(obj)][id(value)]
    except KeyError:
        pass

    for member in dir(obj):
        if getattr(obj, member) == value:
            try:
                member_name_cache[id(obj)][id(value)] = member
            except KeyError:
                member_name_cache[id(obj)] = {id(value): member}
            return member


class SymbolButton(lv.btn):
    def __init__(self, parent, symbol, text):
        super().__init__(parent)
        self.symbol = lv.label(self)
        self.symbol.set_text(symbol)
        self.label = lv.label(self)
        self.label.set_text(text)
        self.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.set_flex_align(lv.FLEX_ALIGN.SPACE_EVENLY, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)


class Page_Buttons:
    def __init__(self, app, page):
        self.app = app
        self.page = page
        self.btn_event_count = {'Play': 0, 'Pause': 0}

        self.page.set_flex_flow(lv.FLEX_FLOW.ROW)
        self.page.set_flex_align(lv.FLEX_ALIGN.SPACE_EVENLY, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.START)

        self.btn1 = SymbolButton(page, lv.SYMBOL.PLAY, "Play")
        self.btn1.set_size(80, 80)

        self.btn2 = SymbolButton(page, lv.SYMBOL.PAUSE, "Pause")
        self.btn2.set_size(80, 80)

        self.label = lv.label(page)
        self.label.add_flag(lv.obj.FLAG.IGNORE_LAYOUT)
        self.label.align(lv.ALIGN.BOTTOM_LEFT, 0, 0)

        def button_cb(event, name):
            self.btn_event_count[name] += 1
            event_name = get_member_name(lv.EVENT, event.code)
            if all((not event_name.startswith(s)) for s in ['DRAW', 'GET', 'STYLE', 'REFR']):
                self.label.set_text('[%d] %s %s' % (self.btn_event_count[name], name, event_name))

        for btn, name in [(self.btn1, 'Play'), (self.btn2, 'Pause')]:
            btn.add_event_cb(lambda event, btn_name=name: button_cb(event, btn_name), lv.EVENT.ALL, None)


class Page_Simple:
    def __init__(self, app, page):
        self.app = app
        self.page = page
        self.test_events = []

        self.page.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.page.set_flex_align(lv.FLEX_ALIGN.SPACE_EVENLY, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)

        # slider
        self.slider = lv.slider(page)
        self.slider.set_width(lv.pct(80))
        self.slider_label = lv.label(page)
        self.slider.add_event_cb(self.on_slider_changed, lv.EVENT.VALUE_CHANGED, None)
        self.on_slider_changed(None)

        # style selector
        self.styles = [('Gray', ColorStyle(0xCCC)),
                       ('Red', ColorStyle(0xF00)),
                       ('Green', ColorStyle(0x0F0)),
                       ('Blue', ColorStyle(0x00F))]

        self.style_selector = lv.dropdown(page)
        self.style_selector.add_style(ShadowStyle(), lv.PART.MAIN)
        self.style_selector.align(lv.ALIGN.OUT_BOTTOM_LEFT, 0, 40)
        self.style_selector.set_options('\n'.join(x[0] for x in self.styles))
        self.style_selector.add_event_cb(self.on_style_selector_changed, lv.EVENT.VALUE_CHANGED, None)

        # counter button
        self.counter_btn = lv.btn(page)
        self.counter_btn.set_size(80, 80)
        self.counter_label = lv.label(self.counter_btn)
        self.counter_label.set_text("Count")
        self.counter_label.align(lv.ALIGN.CENTER, 0, 0)
        self.counter_btn.add_event_cb(self.on_counter_btn, lv.EVENT.CLICKED, None)
        self.counter = 0

    def on_slider_changed(self, event):
        self.slider_label.set_text(str(self.slider.get_value()))

    def on_style_selector_changed(self, event):
        selected = self.style_selector.get_selected()
        tabview = self.app.screen_main.tabview
        if hasattr(self, 'selected_style'): tabview.remove_style(self.selected_style, lv.PART.MAIN)
        self.selected_style = self.styles[selected][1]
        tabview.add_style(self.selected_style, lv.PART.MAIN)

    def on_counter_btn(self, event):
        self.counter += 1
        self.counter_label.set_text(str(self.counter))


class PageTest:
    def __init__(self, app, page):
        self.app = app
        self.page = page
        self.page.set_flex_flow(lv.FLEX_FLOW.ROW)
        self.page.set_flex_align(lv.FLEX_ALIGN.SPACE_EVENLY, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.START)
        self._initialize_buttons()

    def _initialize_buttons(self):
        self.counter_btn = lv.btn(self.page)
        self.counter_btn.set_size(80, 80)
        self.counter_label = lv.label(self.counter_btn)
        self.counter_label.set_text("Count")
        self.counter_label.align(lv.ALIGN.CENTER, 0, 0)
        self.counter_btn.add_event_cb(self.on_counter_btn, lv.EVENT.CLICKED, None)
        self.counter = 0

    def on_counter_btn(self, event):
        self.counter += 1
        self.counter_label.set_text(str(self.counter))


class Screen_Main(lv.obj):
    def __init__(self, app, *args, **kwds):
        self.app = app
        super().__init__(*args, **kwds)
        self.theme = AdvancedDemoTheme()
        self.tabview = lv.tabview(self, lv.DIR.TOP, 20)
        self.page_test = PageTest(self.app, self.tabview.add_tab('Test'))
        self.page_simple = Page_Simple(self.app, self.tabview.add_tab("Simple"))
        self.page_buttons = Page_Buttons(self.app, self.tabview.add_tab("Buttons"))


class AdvancedDemoApplication:
    def init_gui_stm32(self):
        import rk043fn48h as lcd

        hres = 480
        vres = 272

        # Register display driver
        self.event_loop = event_loop()
        lcd.init(w=hres, h=vres)
        disp_buf1 = lv.disp_draw_buf_t()
        buf1_1 = bytearray(hres * 50 * lv.color_t.__SIZE__)
        buf1_2 = bytearray(hres * 50 * lv.color_t.__SIZE__)
        disp_buf1.init(buf1_1, buf1_2, len(buf1_1) // lv.color_t.__SIZE__)
        disp_drv = lv.disp_drv_t()
        disp_drv.init()
        disp_drv.draw_buf = disp_buf1
        disp_drv.flush_cb = lcd.flush
        disp_drv.hor_res = hres
        disp_drv.ver_res = vres
        disp_drv.register()

        # Register touch sensor
        indev_drv = lv.indev_drv_t()
        indev_drv.init()
        indev_drv.type = lv.INDEV_TYPE.POINTER
        indev_drv.read_cb = lcd.ts_read
        indev_drv.register()

    def init_gui(self):

        # Identify platform and initialize it

        if not event_loop.is_running():
            try:
                self.init_gui_stm32()
            except ImportError:
                pass

        # Create the main screen and load it.

        self.screen_main = Screen_Main(self)
        lv.scr_load(self.screen_main)


app = AdvancedDemoApplication()
app.init_gui()
