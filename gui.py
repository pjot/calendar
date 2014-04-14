from gi.repository import Gtk

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
