#!/usr/bin/python

from gi.repository import Gtk, Gio, Gdk
from datetime import date, timedelta

class Month ():
    def __init__ (self, year, month):
        self.year = int(year)
        self.month = int(month)
        my_date = date(self.year, self.month, 1)
        self.name = my_date.strftime('%B')

    def __str__ (self):
        return str(self.year) + ' ' + self.name

    def matches (self, day):
        if isinstance(day, CalendarDay):
            return self.year == day.date.year and self.month == day.date.month
        if isinstance(day, Month):
            return self.year == day.year and self.month == day.month

class EventEditor ():
    def __init__ (self, date):
        self.date = date

        self.window = Gtk.Window()
        app_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Form grid
        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(5)

        # Name field
        grid.attach(Gtk.Label('Name', xalign = 1), 0, 0, 1, 1)
        name_entry = Gtk.Entry()
        name_entry.set_text('Name')
        grid.attach(name_entry, 1, 0, 1, 1)

        # Date field
        grid.attach(Gtk.Label('Date', xalign = 1), 0, 1, 1, 1)
        date_entry = Gtk.Entry()
        date_entry.set_text(date.strftime('%Y-%m-%d'))
        grid.attach(date_entry, 1, 1, 1, 1)

        # Location field
        grid.attach(Gtk.Label('Location', xalign = 1), 0, 2, 1, 1)
        grid.attach(Gtk.Entry(), 1, 2, 1, 1)

        # Button box
        buttons = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)

        # Filler
        buttons.pack_start(Gtk.Label(), True, True, 10)

        # Cancel button
        button = Gtk.Button('Cancel')
        button.connect('clicked', self.close)
        buttons.pack_start(button, False, True, 10)

        # Save button
        button = Gtk.Button('Save')
        button.connect('clicked', self.save)
        buttons.pack_start(button, False, True, 0)

        # Put everything together and show the window
        app_container.pack_start(grid, True, True, 10)
        app_container.pack_start(buttons, False, True, 10)
        app_container.set_margin_left(10)
        app_container.set_margin_right(10)
        self.window.add(app_container)

        self.window.show_all()

    def save (self, *args):
        pass

    def close (self, *args):
        self.window.destroy()

class CalendarDay (Gtk.EventBox):

    def __init__ (self, date):
        Gtk.EventBox.__init__(self)
        self.date = date
        self.label = Gtk.Label()
        # Days should be at least 80
        self.set_size_request(-1, 80)
        self.add(self.label)
        # Add some padding to the date string in the boxes
        self.label.set_alignment(0.1, 0.1)
        self.label.set_hexpand(True)
        self.label.set_vexpand(True)
        self.label.modify_bg(Gtk.StateType.NORMAL, None)
        self.label.set_text('')

    def __eq__ (self, other):
        return self.date.year == other.date.year and self.date.month == other.date.month and self.date.day == other.date.day

    def draw (self, current_month):
        self.label.set_text(self.date.strftime('%d'))
        if self.date == date.today(): 
            self.set_bg(150, 200, 150)
            return
        if current_month.matches(self):
            if self.date.weekday() in [5, 6]:
                self.set_bg(150, 150, 150)
            else:
                self.set_bg(170, 170, 170)
        else:
            self.set_bg(220, 220, 220)

    def set_date (self, date):
        self.date = date
        if self.date.weekday() in [5, 6]:
            # Weekend
            self.set_bg(150, 150, 150)
        else:
            # Regular day
            self.set_bg(170, 170, 170)
        if self.date == date.today():
            # Today
            self.set_bg(150, 200, 150)
        self.label.set_text(date.strftime('%d'))

    def set_bg (self, r, g, b):
        self.label.modify_bg(Gtk.StateType.NORMAL, Gdk.Color.from_floats(r / float(256), g / float(256), b / float(256)))


class MyWindow (Gtk.Window):
    days = ['Week', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

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

        # Year label
        self.label = Gtk.Label()
        self.label.set_text('')
        self.label.set_margin_left(10)
        self.label.set_margin_right(10)
        self.label.set_width_chars(15)
        box.pack_start(self.label, False, False, 10)

        # Month dropdown
        month_store = Gtk.ListStore(int, str)
        for i in range(1, 12):
            month_date = date(2010, i, 1)
            month_store.append([i, month_date.strftime('%B')])
        self.month_dropdown = Gtk.ComboBox.new_with_model(month_store)
        renderer_text = Gtk.CellRendererText()
        self.month_dropdown.pack_start(renderer_text, True)
        # Render the text, but use the number as id
        self.month_dropdown.add_attribute(renderer_text, "text", 1)
        self.month_dropdown.connect("changed", self.month_changed)
        self.month_dropdown.set_property('has-frame', False)
        box.pack_start(self.month_dropdown, False, False, 10)

        # End filler
        box.pack_start(Gtk.Label(), True, True, 10)

        self.app_container.pack_start(box, False, True, 10)

        self.scroller = Gtk.ScrolledWindow()
        self.scroller.set_min_content_height(40)
        self.scroller.connect('scroll-event', self.scrolling)

        # Calendar days
        self.grid = Gtk.Grid()
        self.grid.set_row_spacing(5)
        self.grid.set_column_spacing(5)
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.scroller.add(self.grid)

        # Day names labels
        days_grid = Gtk.Grid()
        days_grid.set_column_spacing(5)
        days_grid.set_row_spacing(0)
        days_grid.set_column_homogeneous(True)

        self.app_container.pack_start(days_grid, False, True, 10)
        self.app_container.pack_start(self.scroller, True, True, 10)

        self.add(self.app_container)

        # Add days labels
        for x in range(0, 8):
            label = Gtk.Label()
            label.set_text(self.days[x])
            label.set_vexpand(False)
            label.set_hexpand(False)
            days_grid.attach(label, x + 1, 0, 1, 1)

        # Add calendar days
        start_date = date(2014, 1, 1)
        day = timedelta(1)
        end_date = date(2015, 1, 1)
        x = 0
        y = 0
        while not start_date.weekday() == 0:
            start_date = start_date - day

        # Loop until we reach the end date
        while start_date < end_date:
            calendar_day = CalendarDay(start_date)
            if x == 6:
                # Add the week number
                week = int(start_date.strftime('%W')) + 1
                self.grid.attach(Gtk.Label(str(week)), 0, y, 1, 1)
            calendar_day.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            calendar_day.connect('button-press-event', self.date_click)
            self.grid.attach(calendar_day, x + 1, y, 1, 1)
            # Iterate!
            start_date = start_date + day
            # Keep track of the coordinates in the grid
            if x == 6:
                x = 0
                y = y + 1
            else:
                x = x + 1

        # Initialize with today
        current_date = date.today()
        self.current_month = Month(current_date.year, current_date.month)
        self.set_month()
        # Trigger the redraw
        self.scrolling()

    def month_changed (self, combo):
        if combo.prevent_default:
            return
        iterator = combo.get_active_iter()
        model = combo.get_model()
        # 0 is the id, 1 is the name
        month = model[iterator][0]
        self.scroll_to(date(self.current_month.year, month, 1))

    def scroll_to (self, date):
        parent_height = self.scroller.get_allocation().height
        # Search for the date
        for day in self.grid.get_children():
            if isinstance(day, Gtk.Label):
                continue
            if day.date == date:
                # Scroll the window
                day_top = day.get_allocation().y - parent_height / 20
                adjustment = self.scroller.get_vadjustment()
                adjustment.set_value(day_top)
                # Render the current month
                self.scrolling()
                return

    def scrolling (self, *args):
        days = {}
        parent_allocation = self.scroller.get_allocation()
        i = 0
        for day in self.grid.get_children():
            # Ignore week number labels
            if isinstance(day, Gtk.Label):
                continue
            # One day per month is enough, speeds up calculation
            if not i == 7:
                i = i + 1
                continue
            i = 0
            # Get coordinates for this day relative to the scroll window
            allocation = day.get_allocation()
            coordinates = day.translate_coordinates(self.scroller, 0, 0)
            day_top = coordinates[1]
            if 0 < day_top + allocation.height and day_top < parent_allocation.height:
                # Day is visible
                year_month = day.date.strftime('%Y-%m')
                # Add to month count
                if not year_month in days.keys():
                    days[year_month] = 1
                else:
                    days[year_month] = days[year_month] + 1

        # Find the month with the most visible days
        year = ''
        month = ''
        current_max = 0
        for ym in days.keys():
            if current_max < days[ym]:
                current_max = days[ym]
                divided = ym.split('-')
                year = divided[0]
                month = divided[1]

        new_month = Month(year, month)
        # Only redraw if the current date has changed
        if not self.current_month.matches(new_month):
            self.current_month = new_month
            self.set_month()

    def date_click (self, calendar_day, event):
        self.scroll_to(calendar_day.date)
#        win = EventEditor(calendar_day.date)

    def set_month (self):
        for day in self.grid.get_children():
            # Ignore week numbers
            if not isinstance(day, CalendarDay):
                continue
            day.draw(self.current_month)
        self.label.set_text(str(self.current_month.year))
        self.month_dropdown.prevent_default = True
        self.month_dropdown.set_active(self.current_month.month - 1)
        self.month_dropdown.prevent_default = False
        self.show_all()

win = MyWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
