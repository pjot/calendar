#!/usr/bin/python

from gi.repository import Gtk, Gio, Gdk
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

class CalendarDay (Gtk.EventBox):

    def __init__ (self, date):
        Gtk.EventBox.__init__(self)
        self.date = date
        self.label = Gtk.Label()
        self.set_size_request(-1, 80)
        self.add(self.label)
        self.label.set_alignment(0.1, 0.1)
        self.label.set_hexpand(True)
        self.label.set_vexpand(True)
        self.clear()

    def draw (self, current_date):
        self.label.set_text(self.date.strftime('%d'))
        if self.date == date.today(): 
            self.set_bg(150, 200, 150)
            return
        if self.date.month == current_date.month and self.date.year == current_date.year:
            if self.date.weekday() in [5, 6]:
                self.set_bg(150, 150, 150)
            else:
                self.set_bg(170, 170, 170)
        else:
            self.set_bg(220, 220, 220)

    def set_date (self, date):
        self.date = date
        if self.date.weekday() in [5, 6]:
            self.set_bg(150, 150, 150)
        else:
            self.set_bg(170, 170, 170)
        if self.date == date.today():
            self.set_bg(150, 200, 150)
        self.label.set_text(date.strftime('%d'))

    def set_bg (self, r, g, b):
        self.label.modify_bg(Gtk.StateType.NORMAL, Gdk.Color.from_floats(r / float(256), g / float(256), b / float(256)))

    def clear (self):
        self.label.modify_bg(Gtk.StateType.NORMAL, None)
        self.label.set_text('')


class MyWindow (Gtk.Window):
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    def dummy (self, *args):
        pass

    def __init__ (self):
        Gtk.Window.__init__(self)

        self.set_border_width(10)
        self.set_default_size(800, 600)

        self.app_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                                                                        
        # Toolbar
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # Initial filler
        box.pack_start(Gtk.Label(), True, True, 10)

        # Left arrow
        button = Gtk.Button()
        button.add(Gtk.Arrow(Gtk.ArrowType.LEFT, Gtk.ShadowType.NONE))
        #button.connect('clicked', self.prev_month)
        #box.pack_start(button, False, False, 10)

        # Month - Year label
        self.label = Gtk.Label()
        self.label.set_text('')
        self.label.set_margin_left(10)
        self.label.set_margin_right(10)
        self.label.set_width_chars(15)
        box.pack_start(self.label, False, False, 10)

        # Right arrow
        button = Gtk.Button()
        button.add(Gtk.Arrow(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE))
        #button.connect('clicked', self.next_month)
        #box.pack_start(button, False, False, 10)

        # End filler
        box.pack_start(Gtk.Label(), True, True, 10)

        self.app_container.pack_start(box, False, True, 10)

        scroller = Gtk.ScrolledWindow()
        scroller.set_min_content_height(40)
        scroller.connect('scroll-event', self.scrolling)
        # Calendar days
        self.grid = Gtk.Grid()
        self.grid.set_row_spacing(5)
        self.grid.set_column_spacing(5)
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        scroller.add(self.grid)

        # Day names labels
        days_grid = Gtk.Grid()
        days_grid.set_column_spacing(5)
        days_grid.set_row_spacing(0)
        days_grid.set_column_homogeneous(True)

        self.app_container.pack_start(days_grid, False, True, 10)
        self.app_container.pack_start(scroller, True, True, 10)

        self.add(self.app_container)

        # Add days labels
        for x in range(0, 7):
            label = Gtk.Label()
            label.set_text(self.days[x])
            label.set_vexpand(False)
            label.set_hexpand(False)
            days_grid.attach(label, x, 0, 1, 1)

        # Add calendar days
        start_date = date(2014, 1, 1)
        day = timedelta(1)
        end_date = date(2015, 1, 1)
        x = 0
        y = 0
        while not start_date.weekday() == 0:
            start_date = start_date - day

        while start_date < end_date:
            calendar_day = CalendarDay(start_date)
            calendar_day.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            calendar_day.connect('button-press-event', self.date_click)
            self.grid.attach(calendar_day, x, y, 1, 1)
            start_date = start_date + day
            if x == 6:
                x = 0
                y = y + 1
            else:
                x = x + 1

        # Initialize with today
        self.current_date = date.today()
        self.set_month()
        self.scrolling(scroller)

    def scrolling (self, scroller, *args):
        days = {}
        parent_allocation = scroller.get_allocation()
        i = 0
        for day in self.grid.get_children():
            if not i == 7:
                i = i + 1
                pass
            i = 0
            allocation = day.get_allocation()
            coordinates = day.translate_coordinates(scroller, 0, 0)
            day_top = coordinates[1]
            if 0 < day_top + allocation.height and day_top < parent_allocation.height:
                # Day is visible
                year_month = day.date.strftime('%Y-%m')
                if not year_month in days.keys():
                    days[year_month] = 1
                else:
                    days[year_month] = days[year_month] + 1

        year = ''
        month = ''
        current_max = 0
        for ym in days.keys():
            if current_max < days[ym]:
                current_max = days[ym]
                divided = ym.split('-')
                year = divided[0]
                month = divided[1]

        new_date = date(int(year), int(month), self.current_date.day)
        if not self.current_date == new_date:
            self.current_date = new_date
            self.set_month()

    def date_click (self, calendar_day, event):
        print calendar_day.date

    def set_month (self):
        for day in self.grid.get_children():
            day.draw(self.current_date)
        self.label.set_text(self.current_date.strftime('%B %Y'))
        self.show_all()

win = MyWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
