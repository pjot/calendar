from gi.repository import Gtk, Gdk
from threading import Timer

import math


class AppContainer(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_margin_left(10)
        self.set_margin_right(10)
        self.set_hexpand(True)
        self.set_vexpand(True)


class FormGrid(Gtk.Grid):
    def __init__(self):
        Gtk.Grid.__init__(self)
        self.set_row_spacing(5)
        self.set_column_spacing(5)
        self.set_hexpand(True)
        self.set_vexpand(True)


class DayGrid(Gtk.Grid):
    def __init__(self):
        Gtk.Grid.__init__(self)
        self.set_row_spacing(5)
        self.set_column_spacing(5)
        self.set_row_homogeneous(True)
        self.set_column_homogeneous(True)


class RightLabel(Gtk.Label):
    def __init__(self, label=None):
        Gtk.Label.__init__(self)
        if label:
            self.set_text(label)
        self.set_property('xalign', 1)


class LeftLabel(Gtk.Label):
    def __init__(self, label=None):
        Gtk.Label.__init__(self)
        if label:
            self.set_text(label)
        self.set_property('xalign', 0)


class TextDropdown(Gtk.ComboBox):
    @staticmethod
    def create(model, column):
        dropdown = TextDropdown()
        dropdown.set_model(model)

        renderer = Gtk.CellRendererText()
        dropdown.pack_start(renderer, True)
        dropdown.add_attribute(renderer, 'text', column)

        return dropdown

    def get_value(self):
        iterator = self.get_active_iter()
        model = self.get_model()
        return model[iterator][0]


class Scroller(Gtk.ScrolledWindow):
    '''
    Check if the Scroller is initialized
    '''
    def is_initialized(self):
        return self.get_vadjustment().get_property('upper') != 1

    '''
    Scroll to a certain value of y. If fast == False, it animates the scrolling
    '''
    def scroll_to(self, y=None, fast=False):
        adjustment = self.get_vadjustment()
        if fast:
            adjustment.set_value(y)
            return
        if y:
            self.target_y = y
            self.current_step = 4
        current_y = adjustment.get_value()
        current_delta = math.fabs(math.fabs(current_y) - self.target_y)
        if self.target_y != current_y:
            if current_delta < self.current_step:
                current_y = self.target_y
            else:
                if current_y > self.target_y:
                    current_y = current_y - self.current_step
                else:
                    current_y = current_y + self.current_step
            adjustment.set_value(current_y)
            if self.current_step < 200:
                self.current_step = self.current_step * 1.4
            Timer(0.02, self.scroll_to).start()


class MessageBar(Gtk.EventBox):
    SHOW_TIME = 0.01
    HIDE_TIME = 0.01
    MAX_HEIGHT = 20
    STEP_SIZE = 1

    def __init__(self, parent):
        Gtk.EventBox.__init__(self)
        self.is_hidden = True
        self.is_animated = False
        self.parent = parent

        color = Gdk.Color.from_floats(120/256.0, 170/256.0, 120/256.0)

        self.label = Gtk.Label()
        self.label.modify_bg(Gtk.StateType.NORMAL, color)
        self.label.set_size_request(-1, self.MAX_HEIGHT)

        self.area = Gtk.DrawingArea()
        self.area.set_size_request(-1, 0)
        self.area.modify_bg(Gtk.StateType.NORMAL, color)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.add(self.area)
        box.add(self.label)

        self.add(box)
        self.connect('show', self.check_visible)

    def check_visible(self, *args):
        if self.is_hidden:
            self.hide()

    def show_message(self, message=None):
        if self.is_animated:
            __, height = self.area.get_size_request()
            if height > self.MAX_HEIGHT:
                self.is_animated = False
                self.area.hide()
                self.area.set_size_request(-1, 0)
                self.label.show()
                self.label.set_text(self.message)
                return
            self.area.set_size_request(-1, height + self.STEP_SIZE)
            Timer(self.SHOW_TIME, self.show_message).start()
            return
        self.is_hidden = False
        self.is_animated = True
        self.message = message + ' (Click to hide)'
        self.label.set_text('')
        self.label.hide()
        self.area.show()
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect('button-press-event', self.hide_message)
        self.show()
        self.set_size_request(-1, 0)
        Timer(self.SHOW_TIME, self.show_message).start()

    def hide_message(self, *args):
        if self.is_animated:
            __, height = self.area.get_size_request()
            if height == 1:
                self.is_animated = False
                self.is_hidden = True
                self.area.hide()
                self.label.hide()
                self.hide()
                self.label.set_text('')
                return
            self.area.set_size_request(-1, height - self.STEP_SIZE)
            Timer(self.HIDE_TIME, self.hide_message).start()
            return
        self.is_animated = True
        self.is_hidden = False
        self.label.set_text('')
        self.label.hide()
        self.area.show()
        self.area.set_size_request(-1, self.MAX_HEIGHT)
        Timer(self.HIDE_TIME, self.hide_message).start()
