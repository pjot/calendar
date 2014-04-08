from gi.repository import Gtk, Gdk
from datetime import date, timedelta, datetime
from dateutil import parser
from threading import Timer
from icalendar import Calendar
from apiclient import discovery
from oauth2client import file
from oauth2client import client
from oauth2client import tools
from event import Event
from config import Config

import math
import sys
import getopt
import argparse
import httplib2
import os


class Week:
    def __init__(self, date):
        self.date = date
        self.set_properties()
        self.one_week = timedelta(7)

    def matches(self, date):
        same_year = self.year == date.year
        same_week = self.week == int(date.strftime('%W'))
        return same_year and same_week

    def set_date(self, date):
        self.date = date
        self.set_properties()

    def set_properties(self):
        self.year = self.date.year
        self.week = int(self.date.strftime('%W')) + 1

    def increase(self):
        self.date = self.date + self.one_week
        self.set_properties()

    def decrease(self):
        self.date = self.date - self.one_week
        self.set_properties()

    def get_text(self):
        return str(self.year) + ' - W' + str(self.week)


class Month:
    def __init__(self, year, month):
        '''
        Creates a Month object which represent a month of a year

        :param year: Year
        :type year: int|str

        :param month: Month
        :type month: int|str
        '''
        self.year = int(year)
        self.month = int(month)
        my_date = date(self.year, self.month, 1)
        self.name = my_date.strftime('%B')

    def matches(self, day):
        '''
        Checks if a day matches this month

        :param day: Day
        :type day: CalendarDay|Month

        :returns: True if the day matches
        :rtype: bool
        '''
        if isinstance(day, CalendarDay):
            return self.year == day.date.year and self.month == day.date.month
        if isinstance(day, Month):
            return self.year == day.year and self.month == day.month


class SettingsEditor:
    def __init__(self, parent):
        self.parent = parent
        self.window = Gtk.Window()

        app_container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            margin_left=10,
            margin_right=10,
            hexpand=True,
            vexpand=True
        )

        # Form grid
        grid = Gtk.Grid(
            row_spacing=5,
            column_spacing=5,
        )

        # Sync with Google?
        grid.attach(Gtk.Label('Google Syncing:', xalign=1), 0, 0, 1, 1)
        self.google_sync = Gtk.Switch(hexpand=False)
        self.google_sync.connect('notify::active', self.toggle_google_button)
        if self.parent.config.get('google_sync'):
            self.google_sync.set_active(True)
        box = Gtk.Box()
        box.add(self.google_sync)
        grid.attach(box, 1, 0, 1, 1)

        # Calendar name
        self.calendar_name = self.parent.config.get('calendar_name')
        self.calendar_id = self.parent.config.get('calendar_id')
        calendar_box = Gtk.Box()
        grid.attach(Gtk.Label('Calendar:', xalign=1), 0, 1, 1, 1)
        self.calendar_label = Gtk.Label(self.calendar_name, xalign=0)
        calendar_box.add(self.calendar_label)
        grid.attach(calendar_box, 1, 1, 1, 1)

        # Calendar dropdown
        self.calendar_store = Gtk.ListStore(int, str, str)
        self.calendar_dropdown = Gtk.ComboBox.new_with_model(self.calendar_store)
        renderer_text = Gtk.CellRendererText()
        self.calendar_dropdown.pack_start(renderer_text, True)
        self.calendar_dropdown.add_attribute(renderer_text, "text", 2)
        self.calendar_dropdown.connect('changed', self.calendar_change)
        calendar_box.add(self.calendar_dropdown)

        # Button box
        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # Filler
        buttons.pack_start(Gtk.Label(), True, True, 10)

        # Fetch button
        fetch_button = Gtk.Button('Fetch')
        fetch_button.connect('clicked', self.fetch_calendars)
        buttons.pack_start(fetch_button, False, True, 0)

        # Cancel button
        button = Gtk.Button('Cancel')
        button.connect('clicked', self.close)
        buttons.pack_start(button, False, True, 10)

        # Save button
        button = Gtk.Button('Save')
        button.connect('clicked', self.save)
        buttons.pack_start(button, False, True, 0)

        app_container.pack_start(grid, False, False, 10)
        app_container.pack_start(buttons, False, False, 10)

        self.window.add(app_container)
        self.window.show_all()
        self.calendar_dropdown.hide()

    def fetch_calendars(self, *args):
        google_client = self.parent.get_google_client()
        self.calendar_store.clear()
        calendars = google_client.get_calendars()
        for i, calendar in enumerate(calendars['items']):
            self.calendar_store.append([i, calendar['id'], calendar['summary']])

        self.calendar_dropdown.show()
        self.calendar_label.hide()
        self.calendar_dropdown.set_active(0)

    def calendar_change(self, combo, *args):
        iterator = combo.get_active_iter()
        model = combo.get_model()
        # 1 is the id, 2 is the name
        self.calendar_name = model[iterator][2]
        self.calendar_id = model[iterator][1]

    def toggle_google_button(self, switch, *args):
        if switch.get_active():
            self.parent.google_button.set_sensitive(True)
        else:
            self.parent.google_button.set_sensitive(False)

    def close(self, *args):
        self.window.destroy()
        self.parent.toggle_google_button()

    def save(self, *args):
        config = self.parent.config
        config.set('google_sync', self.google_sync.get_active())
        config.set('calendar_name', self.calendar_name)
        config.set('calendar_id', self.calendar_id)
        config.save()
        self.window.destroy()
        self.parent.toggle_google_button()


class EventEditor:
    def __init__(self, event, initiator):
        '''
        Creates an Event edit window

        :param date: Default date
        :type date: date
        '''
        self.event = event
        self.date = event.date
        self.initiator = initiator

        self.window = Gtk.Window()
        self.window.set_size_request(400, 400)
        app_container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            margin_left=10,
            margin_right=10,
            hexpand=True,
            vexpand=True
        )

        # Form grid
        grid = Gtk.Grid(
            row_spacing=5,
            column_spacing=5,
            hexpand=True,
            vexpand=True
        )

        # Name field
        grid.attach(Gtk.Label('Name:', xalign=1), 0, 0, 1, 1)
        self.name_entry = Gtk.Entry(hexpand=True)
        self.name_entry.set_text(self.event.name)
        grid.attach(self.name_entry, 1, 0, 1, 1)

        # Date field
        grid.attach(Gtk.Label('Date:', xalign=1), 0, 1, 1, 1)
        self.date_entry = Gtk.Entry(hexpand=True)
        self.date_entry.set_text(self.date.strftime('%Y-%m-%d'))
        grid.attach(self.date_entry, 1, 1, 1, 1)

        # Time fields
        start_time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        end_time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # Hours
        renderer_text = Gtk.CellRendererText()
        hour_store = Gtk.ListStore(int, str)
        for hour in range(0, 24):
            padded = str(hour)
            if hour < 10:
                padded = '0' + padded
            hour_store.append([hour, padded])

        self.start_hour_dropdown = Gtk.ComboBox.new_with_model(hour_store)
        self.start_hour_dropdown.pack_start(renderer_text, True)
        self.start_hour_dropdown.add_attribute(renderer_text, 'text', 1)
        self.start_hour_dropdown.set_property('has-frame', False)
        self.start_hour_dropdown.set_active(self.event.start_hour)
        start_time_box.add(self.start_hour_dropdown)

        self.end_hour_dropdown = Gtk.ComboBox.new_with_model(hour_store)
        self.end_hour_dropdown.pack_end(renderer_text, True)
        self.end_hour_dropdown.add_attribute(renderer_text, 'text', 1)
        self.end_hour_dropdown.set_property('has-frame', False)
        self.end_hour_dropdown.set_active(self.event.end_hour)
        end_time_box.add(self.end_hour_dropdown)

        # Separator
        start_time_box.pack_start(Gtk.Label(':'), False, False, 5)
        end_time_box.pack_start(Gtk.Label(':'), False, False, 5)

        # Minutes
        minute_store = Gtk.ListStore(int, str)
        for minute in range(0, 60):
            padded = str(minute)
            if minute < 10:
                padded = '0' + padded
            minute_store.append([minute, padded])

        self.start_minute_dropdown = Gtk.ComboBox.new_with_model(minute_store)
        self.start_minute_dropdown.pack_start(renderer_text, True)
        self.start_minute_dropdown.add_attribute(renderer_text, 'text', 1)
        self.start_minute_dropdown.set_property('has-frame', False)
        self.start_minute_dropdown.set_active(self.event.start_minute)
        start_time_box.add(self.start_minute_dropdown)

        self.end_minute_dropdown = Gtk.ComboBox.new_with_model(minute_store)
        self.end_minute_dropdown.pack_start(renderer_text, True)
        self.end_minute_dropdown.add_attribute(renderer_text, 'text', 1)
        self.end_minute_dropdown.set_property('has-frame', False)
        self.end_minute_dropdown.set_active(self.event.end_minute)
        end_time_box.add(self.end_minute_dropdown)

        grid.attach(Gtk.Label('Start Time:', xalign=1), 0, 2, 1, 1)
        grid.attach(start_time_box, 1, 2, 1, 1)

        grid.attach(Gtk.Label('End Time:', xalign=1), 0, 3, 1, 1)
        grid.attach(end_time_box, 1, 3, 1, 1)

        # Location field
        grid.attach(Gtk.Label('Location:', xalign=1), 0, 4, 1, 1)
        self.location_entry = Gtk.Entry(hexpand=True)
        self.location_entry.set_text(self.event.location)
        grid.attach(self.location_entry, 1, 4, 1, 1)

        # Button box
        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

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
        self.window.add(app_container)

        self.window.show_all()

    def save(self, *args):
        '''
        Saves the event and closes the window
        '''
        event = self.event
        event.name = self.name_entry.get_text()
        event.location = self.location_entry.get_text()
        date = self.date_entry.get_text()
        event.date = datetime.strptime(date, '%Y-%m-%d').date()

        iterator = self.start_hour_dropdown.get_active_iter()
        model = self.start_hour_dropdown.get_model()
        event.start_hour = model[iterator][0]

        iterator = self.start_minute_dropdown.get_active_iter()
        model = self.start_minute_dropdown.get_model()
        event.start_minute = model[iterator][0]

        iterator = self.end_hour_dropdown.get_active_iter()
        model = self.end_hour_dropdown.get_model()
        event.end_hour = model[iterator][0]

        iterator = self.end_minute_dropdown.get_active_iter()
        model = self.end_minute_dropdown.get_model()
        event.end_minute = model[iterator][0]

        if self.initiator.parent.parent.config.get('google_sync'):
            google = self.initiator.parent.parent.get_google_client()
            google.set_calendar_id()
            google.export_event(event)
        event.save()

        self.initiator.add_event(event)
        self.initiator.refresh_events()
        # Give the click event back to the Initiator
        self.initiator.is_blocked = False
        self.initiator.parent.update_gui()
        self.initiator.parent.parent.show_message('Successfully added event')
        self.window.destroy()

    def close(self, *args):
        '''
        Closes the window
        '''
        self.initiator.is_blocked = False
        self.window.destroy()


class CalendarDisplay(Gtk.EventBox):
    def set_bg(self, color):
        '''
        Set the background of the box. Accepts ints between 0 and 256.

        :param color: Color tuple (red, green, blue)
        :type color: tuple
        '''
        red = color[0] / float(256)
        green = color[1] / float(256)
        blue = color[2] / float(256)
        color = Gdk.Color.from_floats(red, green, blue)
        self.modify_bg(Gtk.StateType.NORMAL, color)

    def add_event(self, event):
        for each in self.events:
            if each.id == event.id:
                return
        self.events.add(event)

    def _edit_event(self, area, *args):
        self.is_blocked = True
        EventEditor(Event.get_by_id(area.event_id), self)


class CalendarHour(CalendarDisplay):

    #                    r    g    b
    OTHER_DAY        = (220, 220, 220)
    BUSINESS_DAY     = (170, 170, 170)
    OTHER_WEEKEND    = (200, 200, 200)
    BUSINESS_WEEKEND = (150, 150, 150)
    OTHER_TODAY      = (150, 200, 150)
    BUSINESS_TODAY   = (120, 170, 120)

    def __init__(self, date, hour, parent):
        CalendarDisplay.__init__(self)
        self.date = date
        self.hour = hour
        self.parent = parent
        self.is_blocked = False

        self.set_events()

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.label = Gtk.Label()
        self.grid = Gtk.Grid()
        self.label.set_alignment(0.1, 0.1)
        if self.date.weekday() == 0:
            self.main_box.pack_start(self.label, False, False, 5)
        self.main_box.add(self.grid)
        self.set_size_request(-1, 40)
        self.add(self.main_box)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.draw()
        self.refresh_events()

    def set_events(self):
        self.events = set()
        events = Event.get_by_hour(
            self.date.year,
            self.date.month,
            self.date.day,
            self.hour,
        )
        for event in events:
            self.add_event(event)

    def refresh_events(self):
        '''
        Refresh the events in the view
        '''
        # Remove all widgets
        for widget in self.grid.get_children():
            widget.destroy()
        # Re-add them
        self.set_events()
        for i, event in enumerate(self.events):
            area = EventDisplay()
            area.event_id = event.id
            area.connect('button-press-event', self._edit_event)
            # Add 5 events per row
            self.grid.attach(area, i % 5, i / 5, 1, 1)
        self.grid.show_all()

    def draw(self):
        if self.date.weekday() == 0:
            self.label.set_text(str(self.hour) + ':00')

        if self.hour > 8 and self.hour < 18:
            if self.date == date.today():
                self.set_bg(self.BUSINESS_TODAY)
                return
            if self.date.weekday() in [5, 6]:
                self.set_bg(self.BUSINESS_WEEKEND)
            else:
                self.set_bg(self.BUSINESS_DAY)
        else:
            if self.date == date.today():
                self.set_bg(self.OTHER_TODAY)
                return
            if self.date.weekday() in [5, 6]:
                self.set_bg(self.OTHER_WEEKEND)
            else:
                self.set_bg(self.OTHER_DAY)


class EventDisplay(Gtk.DrawingArea):

    def __init__(self, *args):
        Gtk.DrawingArea.__init__(self)
        self.set_margin_top(5)
        self.set_margin_left(5)
        self.set_size_request(15, 15)
        color = Gdk.Color.from_floats(0.2, 0.5, 0.2)
        self.modify_bg(Gtk.StateType.NORMAL, color)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)


class CalendarDay(CalendarDisplay):

    #                r    g    b
    EVEN_DAY     = (220, 220, 220)
    EVEN_WEEKEND = (200, 200, 200)
    ODD_DAY      = (170, 170, 170)
    ODD_WEEKEND  = (150, 150, 150)
    TODAY        = (150, 200, 150)

    ODD = (1, 3, 5, 7, 9, 11)

    def __init__(self, date, parent):
        '''
        Creates a CalendarDay object that represents a box in the main view.

        :param date: Date
        :type date: date
        '''
        CalendarDisplay.__init__(self)
        self.date = date
        self.parent = parent
        self.is_blocked = False

        self.set_events()

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.grid = Gtk.Grid(row_spacing=5)

        self.label = Gtk.Label(hexpand=True)
        self.week_label = Gtk.Label(margin_right=5)
        label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label_box.add(self.label)
        label_box.add(self.week_label)
        self.main_box.add(label_box)
        self.main_box.add(self.grid)
        # Days should be at least 80
        self.set_size_request(-1, 80)
        self.add(self.main_box)
        self.set_hexpand(True)
        self.set_vexpand(True)
        # Add some padding to the date string in the boxes
        self.label.set_alignment(0.05, 0.1)
        self.week_label.set_alignment(0.95, 0.9)
        self.label.modify_bg(Gtk.StateType.NORMAL, None)
        self.label.set_text('')
        self.refresh_events()

    def set_events(self):
        self.events = set()
        events = Event.get_by_day(
            self.date.year,
            self.date.month,
            self.date.day
        )
        for event in events:
            self.add_event(event)

    def refresh_events(self):
        '''
        Refresh the events in the view
        '''
        # Remove all widgets
        for widget in self.grid.get_children():
            widget.destroy()
        # Re-add them
        self.set_events()
        for i, event in enumerate(self.events):
            area = Gtk.DrawingArea(margin_left=5)
            area.set_size_request(15, 15)
            color = Gdk.Color.from_floats(0.2, 0.5, 0.2)
            area.modify_bg(Gtk.StateType.NORMAL, color)
            area.event_id = event.id
            area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            area.connect('button-press-event', self._edit_event)
            # Add 5 events per row
            self.grid.attach(area, i % 5, i / 5, 1, 1)

    def __eq__(self, other):
        '''
        Enables comparisons with other CalendarDays

        :param other: Other object
        :type other: CalendarDay

        :returns bool: True if the date matches
        '''
        same_year = self.date.year == other.date.year
        same_month = self.date.month == other.date.month
        same_day = self.date.day == other.date.day
        return same_year and same_month and same_day

    def draw(self, current_month):
        '''
        Sets the color based upon the current month in the view

        :param current_month: Current month
        :type current_month: Month
        '''
        week_text = ''
        day_text = ''
        if self.date.year == self.parent.parent.year:
            day_text = self.date.strftime('%d')
            if self.date.weekday() == 6:
                week_text = str(int(self.date.strftime('%W')) + 1)
        else:
            self.label.set_text('')
            self.label.modify_bg(Gtk.StateType.NORMAL, None)
            return
        self.label.set_text(day_text)
        self.week_label.set_markup('<b>' + week_text + '</b>')
        if self.date == date.today():
            # Day is today
            self.set_bg(self.TODAY)
            return
        if self.date.month in self.ODD:
            if self.date.weekday() in [5, 6]:
                self.set_bg(self.ODD_WEEKEND)
            else:
                self.set_bg(self.ODD_DAY)
        else:
            if self.date.weekday() in [5, 6]:
                self.set_bg(self.EVEN_WEEKEND)
            else:
                self.set_bg(self.EVEN_DAY)


class WeekView(Gtk.Box):
    days = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    def __init__(self, parent):
        Gtk.Box.__init__(self)
        self.parent = parent
        self.is_new = True

        self.one_day = timedelta(1)

        self.scroller = Scroller(min_content_height=40)
        self.scroller.connect('size-allocate', self.initial_scroll)

        self.parent.previous_button.connect('clicked', self.decrease)
        self.parent.next_button.connect('clicked', self.increase)
        self.parent.this_week_button.connect('clicked', self.this_week)

        self.grid = Gtk.Grid(
            column_spacing=5,
            row_spacing=5,
            column_homogeneous=True,
            row_homogeneous=True,
        )

        self.scroller.add(self.grid)
        self.add(self.scroller)

        self.current_week = Week(date.today())
        self.add_days()
        self.update_gui()

    def decrease(self, *args):
        self.current_week.decrease()
        self.add_days()
        self.update_gui()

    def this_week(self, *args):
        self.current_week.set_date(date.today())
        self.add_days()
        self.update_gui()

    def increase(self, *args):
        self.current_week.increase()
        self.add_days()
        self.update_gui()

    def update_days(self):
        first_date = self.get_first_date()
        days = []
        for day in range(0, 7):
            days.append(self.days[day] + ' ' + first_date.strftime('%d'))
            first_date = first_date + self.one_day
        self.parent.set_day_labels(days)

    def get_first_date(self):
        first_date = self.current_week.date

        while first_date.weekday() != 0:
            first_date = first_date - self.one_day

        return first_date

    def add_days(self):
        first_date = self.get_first_date()

        for widget in self.grid.get_children():
            widget.destroy()

        # Add all hours in the week
        for day in range(0, 7):
            for hour in range(0, 23):
                calendar_hour = CalendarHour(first_date, hour, self)
                calendar_hour.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
                calendar_hour.connect('button-press-event', self.hour_click)
                calendar_hour.date = first_date
                self.grid.attach(calendar_hour, day, hour, 1, 1)
            first_date = first_date + self.one_day

    def hour_click(self, calendar_hour, *args):
        if not calendar_hour.is_blocked:
            event = Event()
            event.date = calendar_hour.date
            event.start_hour = calendar_hour.hour
            event.start_minute = 0
            event.end_hour = calendar_hour.hour + 1
            event.end_minute = 0
            EventEditor(event, calendar_hour)

    def initial_scroll(self, *args):
        if self.is_new and self.scroller.is_initialized():
            self.scroller.scroll_to(8 * 45 - 5, fast=True)
            self.is_new = False

    def update_gui(self):
        self.update_days()
        self.grid.show_all()
        self.parent.week_label.set_text(self.current_week.get_text())
        for calendar_hour in self.grid.get_children():
            calendar_hour.refresh_events()


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


class FlexView(Gtk.Box):
    days = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    def __init__(self, parent):
        '''
        Creates a Flex View.

        The Flex View is a view that displays an entire year with one box per
        day. It shades the months in different colors and allows the user to
        scroll through the weeks.

        :param parent: Parent window
        :type parent: CalendarWindow
        '''
        Gtk.Box.__init__(self)
        self.is_new = True
        self.parent = parent
        self.scroller = Scroller(min_content_height=40)
        self.scroller.connect('size-allocate', self.initial_scroll)

        # Calendar days
        self.grid = Gtk.Grid(
            row_spacing=5,
            column_spacing=5,
            row_homogeneous=True,
            column_homogeneous=True,
        )
        self.scroller.add(self.grid)

        self.add(self.scroller)

        self.scroller.connect('scroll-event', self.scrolling)
        self.parent.month_dropdown.connect('changed', self.month_changed)
        self.parent.year_dropdown.connect('changed', self.year_changed)
        self.parent.today_button.connect('clicked', self.goto_today)

        current_date = date.today()
        self.current_month = Month(current_date.year, current_date.month)
        self.set_year(current_date.year)

    def year_changed(self, combo):
        '''
        When the year is changed we should scroll to the new year

        :param combo: The year dropdown
        :type combo: Gtk.ComboBox
        '''
        if self.prevent_default:
            return
        iterator = combo.get_active_iter()
        model = combo.get_model()
        # 0 is the id, 1 is the name
        year = model[iterator][0]
        self.set_year(year)

    def set_year(self, year):
        year = int(year)
        # Prevent redrawing the same year
        if year == self.parent.year:
            return
        # Clear the CalendarDays
        for widget in self.grid.get_children():
            widget.destroy()
        # Add calendar days
        self.parent.year = year
        start_date = date(self.parent.year, 1, 1)
        day = timedelta(1)
        end_date = date(self.parent.year, 12, 31)
        x = 0
        y = 0
        while not start_date.weekday() == 0:
            start_date = start_date - day

        # Loop until we reach the end date
        while start_date < end_date:
            calendar_day = CalendarDay(start_date, self)
            if start_date.year == self.parent.year:
                calendar_day.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
                calendar_day.connect('button-press-event', self.date_click)
            self.grid.attach(calendar_day, x, y, 1, 1)
            # Iterate!
            start_date = start_date + day
            # Keep track of the coordinates in the grid
            if x == 6:
                x = 0
                y = y + 1
            else:
                x = x + 1

        self.current_month.year = self.parent.year
        self.draw()
        self.update_gui()

    def month_changed(self, combo):
        '''
        When the month is changed we should scroll to the new month

        :param combo: The month dropdown
        :type combo: Gtk.ComboBox
        '''
        if self.prevent_default:
            return
        iterator = combo.get_active_iter()
        model = combo.get_model()
        # 0 is the id, 1 is the name
        month = model[iterator][0]
        self.scroll_to(date(self.current_month.year, month, 1))

    def goto_today(self, *args):
        today = date.today()
        self.set_year(today.year)
        self.show_all()
        self.scroll_to(today)

    def initial_scroll(self, *args):
        if self.is_new and self.scroller.is_initialized():
            day_in_year = int(date.today().strftime('%j')) / 7
            scroll_top = day_in_year * 85 - 20
            self.scroller.scroll_to(scroll_top, fast=True)
            self.is_new = False

    def update_days(self):
        self.parent.set_day_labels(self.days)

    def scroll_to(self, to_date):
        '''
        Scrolls to a date by putting it at the top

        :param date: Date
        :type date: date
        '''
        day_in_year = int(to_date.strftime('%j')) + 1
        rows = day_in_year / 7
        day_top = rows * 85 - 20
        self.scroller.scroll_to(day_top)
        self.current_month.month = to_date.month
        self.current_month.year = to_date.year
        self.draw()
        self.update_gui()

    def get_calendar_day(self, date):
        '''
        Returns the CalendarDay of a date

        :param date: Date
        :type date: date

        :returns CalendarDay: The CalendarDay
        '''
        for day in self.grid.get_children():
            if day.date == date:
                return day

    def scrolling(self, *args):
        '''
        Calculates the current active month and updates the GUI accordingly
        '''
        days = {}
        parent_allocation = self.scroller.get_allocation()
        i = 0
        for day in self.grid.get_children():
            # One day per week is enough, speeds up calculation
            if not i == 7:
                i = i + 1
                continue
            i = 0
            # Get coordinates for this day relative to the scroll window
            allocation = day.get_allocation()
            coordinates = day.translate_coordinates(self.scroller, 0, 0)
            if coordinates:
                day_top = coordinates[1]
            else:
                day_top = 0

            above = 0 < day_top + allocation.height
            below = day_top < parent_allocation.height
            if above and below:
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
            self.update_gui()

    def date_click(self, calendar_day, *args):
        '''
        Open an Event edit window for a CalendarDay

        :param calendar_day: The CalendarDay
        :type calendar_day: CalendarDay
        '''
        if not calendar_day.is_blocked:
            event = Event()
            event.date = calendar_day.date
            now = datetime.now()
            event.start_hour = now.hour
            event.end_hour = now.hour + 1
            event.start_minute = 0
            event.end_minute = 0
            EventEditor(event, calendar_day)

    def draw(self):
        for day in self.grid.get_children():
            day.draw(self.current_month)

    def update_gui(self):
        '''
        Updates the GUI using the current active month
        '''
        self.prevent_default = True
        active_year = self.current_month.year - self.parent.START_YEAR
        self.parent.year_dropdown.set_active(active_year)
        self.parent.month_dropdown.set_active(self.current_month.month - 1)
        self.prevent_default = False

        for calendar_day in self.grid.get_children():
            calendar_day.refresh_events()
        self.parent.show_all()


class CalendarWindow(Gtk.Window):
    days = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    START_YEAR = 2010
    END_YEAR = 2020

    CONFIG_DIR = '.config/pjot-calendar'

    def __init__(self):
        '''
        Creates a new Window and fills it with the interface
        '''
        Gtk.Window.__init__(self)

        self.CONFIG_DIR = os.path.join(os.getenv('HOME'), self.CONFIG_DIR)
        self.google_client = None

        # Ensure that a config directory exists
        if not os.path.isdir(self.CONFIG_DIR):
            os.makedirs(self.CONFIG_DIR)

        Event.CONFIG_DIR = self.CONFIG_DIR

        self.config = Config(self.CONFIG_DIR)

        self.set_icon_from_file(os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'images/evolution-calendar.svg'
        ))
        self.set_title('Calendar')
        self.set_border_width(10)
        self.set_default_size(800, 600)
        self.year = 0
        self.show_week_dropdown = False
        self.app_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Message bar
        self.message_bar = MessageBar(self)

        # Toolbar
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # View toolbar
        self.toolbar = Gtk.Box()
        self.flex_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.week_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # Year dropdown
        year_store = Gtk.ListStore(int, str)
        for year in range(self.START_YEAR, self.END_YEAR):
            year_store.append([year, str(year)])
        self.year_dropdown = Gtk.ComboBox.new_with_model(year_store)
        renderer_text = Gtk.CellRendererText()
        self.year_dropdown.pack_start(renderer_text, True)
        self.year_dropdown.add_attribute(renderer_text, 'text', 1)
        self.year_dropdown.set_property('has-frame', False)
        self.flex_box.pack_start(self.year_dropdown, False, False, 0)

        # Month dropdown
        month_store = Gtk.ListStore(int, str)
        for i in range(1, 13):
            month_date = date(2010, i, 1)
            month_store.append([i, month_date.strftime('%B')])
        self.month_dropdown = Gtk.ComboBox.new_with_model(month_store)
        renderer_text = Gtk.CellRendererText()
        self.month_dropdown.pack_start(renderer_text, True)
        # Render the text, but use the number as id
        self.month_dropdown.add_attribute(renderer_text, "text", 1)
        self.month_dropdown.set_property('has-frame', False)
        self.flex_box.pack_start(self.month_dropdown, False, False, 10)

        # Today button
        self.today_button = Gtk.Button('Today')
        self.this_week_button = Gtk.Button('Today')
        self.flex_box.pack_start(self.today_button, False, False, 0)

        # Week arrow left
        self.previous_button = Gtk.Button()
        left_arrow = Gtk.Arrow(Gtk.ArrowType.LEFT, Gtk.ShadowType.NONE)
        self.previous_button.add(left_arrow)
        self.week_box.pack_start(self.previous_button, False, False, 0)

        # Week arrow right
        self.next_button = Gtk.Button()
        right_arrow = Gtk.Arrow(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE)
        self.next_button.add(right_arrow)
        self.week_box.pack_start(self.next_button, False, False, 0)

        self.week_box.pack_start(self.this_week_button, False, False, 10)

        # Week label
        self.week_label = Gtk.Label()
        self.week_box.pack_start(self.week_label, False, False, 0)

        # View buttons
        self.stack = Gtk.Stack(
            transition_duration=100,
            transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT,
        )
        self.stack_switcher = Gtk.StackSwitcher(stack=self.stack)
        event_box = Gtk.EventBox(above_child=True)
        event_box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        event_box.connect('button-press-event', self.switcher_click)
        event_box.add(self.stack_switcher)

        # Toolbar
        self.toolbar.add(self.week_box)
        box.pack_start(self.toolbar, True, True, 0)

        # File button
        file_button = Gtk.Button.new_from_icon_name(
            'list-add', Gtk.IconSize.MENU
        )
        file_button.connect('clicked', self.file_button)
        box.pack_start(file_button, False, False, 0)

        # Google button
        self.google_button = Gtk.Button.new_from_icon_name(
            Gtk.STOCK_REFRESH, Gtk.IconSize.MENU
        )
        self.google_button.connect('clicked', self.import_from_google)
        box.pack_start(self.google_button, False, False, 0)

        # Settings button
        settings_button = Gtk.Button.new_from_icon_name(
            Gtk.STOCK_PREFERENCES, Gtk.IconSize.MENU
        )
        settings_button.set_margin_right(10)
        settings_button.connect('clicked', self.settings_editor)
        box.pack_start(settings_button, False, False, 0)

        box.pack_start(event_box, False, False, 0)
        self.app_container.pack_start(box, False, True, 0)

        # Day names labels
        self.days_grid = Gtk.Grid(
            column_spacing=5,
            row_spacing=0,
            column_homogeneous=True,
            margin_right=15,
        )
        self.app_container.pack_start(self.days_grid, False, True, 5)

        # Add views
        self.week_view = WeekView(self)
        self.stack.add_titled(self.week_view, 'week', 'Week')

        self.flex_view = FlexView(self)
        self.stack.add_titled(self.flex_view, 'flex', 'Flex')

        self.current_view = self.week_view
        self.current_view.update_days()

        self.app_container.pack_start(self.stack, False, True, 5)

        # Message bar
        self.app_container.pack_start(self.message_bar, False, True, 5)

        self.add(self.app_container)
        self.show_all()
        self.message_bar.hide()

    def toggle_google_button(self):
        if not self.config.get('google_sync'):
            self.google_button.set_sensitive(False)
        else:
            self.google_button.set_sensitive(True)

    def show_all(self, *args):
        Gtk.Window.show_all(self)
        self.toggle_google_button()

    def show_message(self, message):
        self.message_bar.show_message(message)

    def switcher_click(self, __, event):
        '''
        Somewhat hacky way of catching clicks in the stack switcher by
        comparing the click's x to the middle of the switcher. The first half
        of the switcher is the Week button and the second half is the Flex
        button.
        '''
        allocation = self.stack_switcher.get_allocation()
        if allocation.width / 2 < event.x:
            self.set_view('flex')
        else:
            self.set_view('week')

    def set_view(self, view):
        self.stack.set_visible_child_name(view)

        for widget in self.toolbar.get_children():
            self.toolbar.remove(widget)

        if view == 'week':
            self.current_view = self.week_view
            self.toolbar.add(self.week_box)
        else:
            self.current_view = self.flex_view
            self.toolbar.add(self.flex_box)

        self.current_view.initial_scroll()
        self.current_view.update_days()
        self.current_view.update_gui()
        self.toolbar.show_all()

    def settings_editor(self, *args):
        SettingsEditor(self)

    def get_google_client(self):
        if self.google_client is None:
            self.google_client = Google(self)
        return self.google_client

    def import_from_google(self, *args):
        google = self.get_google_client()
        google.set_calendar_id()
        google.import_events()

    def file_button(self, *args):
        dialog = Gtk.FileChooserDialog(
            "Please choose a file",
            self,
            Gtk.FileChooserAction.OPEN,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK
            )
        )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.open_file(dialog.get_filename())
        dialog.destroy()

    def open_file(self, file_path):
        with open(file_path) as f:
            data = f.read()
        cal = Calendar.from_ical(data)
        for component in cal.walk():
            if component.name == 'VEVENT':
                name = component.get('summary')
                start = component.get('dtstart').dt
                end = component.get('dtend').dt
                location = component.get('location')
                event = Event()
                event.name = name
                event.location = location
                event.year = start.year
                event.month = start.month
                event.day = start.day
                event.start_hour = int(start.strftime('%H'))
                event.start_minute = int(start.strftime('%M'))
                event.end_hour = int(end.strftime('%H'))
                event.end_minute = int(end.strftime('%M'))
                event.save()
                self.show_message('Successfully added event')
                self.current_view.update_gui()

    def set_day_labels(self, labels):
        for widget in self.days_grid:
            widget.destroy()

        for x, day in enumerate(labels):
            label = Gtk.Label(vexpand=False, hexpand=False)
            label.set_text(day)
            self.days_grid.attach(label, x + 1, 0, 1, 1)
        self.days_grid.show_all()


class Google:
    def __init__(self, parent):
        self.calendar_id = None
        self.parent = parent
        arg_parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            parents=[tools.argparser]
        )
        flags = arg_parser.parse_args([])
        self.CLIENT_SECRETS = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                'client_secrets.json'
        )
        self.FLOW = client.flow_from_clientsecrets(
            self.CLIENT_SECRETS,
            scope=[
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/calendar.readonly',
            ],
            message=tools.message_if_missing(self.CLIENT_SECRETS)
        )

        data_file = os.path.join(self.parent.CONFIG_DIR, 'google-calendar.dat')
        storage = file.Storage(data_file)
        credentials = storage.get()
        if credentials is None or credentials.invalid:
            credentials = tools.run_flow(self.FLOW, storage, flags)

        http = httplib2.Http()
        http = credentials.authorize(http)

        self.service = discovery.build('calendar', 'v3', http=http)

    def get_calendars(self):
        return self.service.calendarList().list().execute()

    def set_calendar_id(self):
        calendars = self.get_calendars()
        for item in calendars['items']:
            if item['id'] == self.parent.config.get('calendar'):
                self.calendar_id = item['id']

    def export_event(self, event):
        if self.calendar_id is None:
            return event

        if event.google_id:
            self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event.google_id,
                body=event.to_google()
            ).execute()
        else:
            response = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event.to_google()
            ).execute()
            event.google_id = response['id']
        return event

    def import_events(self):

        request = self.service.events().list(calendarId=self.calendar_id)
        events = request.execute()

        items = 0
        for item in events['items']:
            event = Event.get_by_google_id(item['id'])

            if 'dateTime' in item['start']:
                start_dt = parser.parse(item['start']['dateTime'])
            else:
                start_dt = parser.parse(item['start']['date'])

            if 'dateTime' in item['end']:
                end_dt = parser.parse(item['end']['dateTime'])
                event.end_hour = end_dt.hour
                event.end_minute = end_dt.minute
            else:
                end_dt = parser.parse(item['end']['date'])
                event.end_hour = 23
                event.end_minute = 59

            event.year = start_dt.year
            event.month = start_dt.month
            event.day = start_dt.day
            event.start_hour = start_dt.hour
            event.start_minute = start_dt.minute

            event.google_id = item['id']
            event.name = item['summary']
            if 'location' in item:
                event.location = item['location']

            event.save()
            items = items + 1
        message = 'Successfully imported {} items'.format(items)
        self.parent.show_message(message)


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


win = CalendarWindow()
win.connect("delete-event", Gtk.main_quit)

opts, args = getopt.getopt(sys.argv[1:], 'i', ['import='])
for opt, arg in opts:
    if opt in ('-i', '--import'):
        win.open_file(arg)

Gtk.main()
