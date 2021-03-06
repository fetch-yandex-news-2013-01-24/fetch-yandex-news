#!/usr/bin/env python3
# -*- mode: python; coding: utf-8 -*-
#
# Copyright 2013 Andrej A Antonov <polymorphm@gmail.com>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

assert str is not bytes

import threading
import tkinter
from tkinter import ttk, scrolledtext, filedialog
from . import tk_mt, tk_async
from .. import read_list, fetch_news

DEFAULT_MAIN_WINDOW_WIDTH = 700
DEFAULT_MAIN_WINDOW_HEIGHT = 500

class MainWindow:
    def __init__(self):
        self._root = tkinter.Tk()
        self._tk_mt = tk_mt.TkMt(self._root)
        self._root.protocol('WM_DELETE_WINDOW', self._close_cmd)
        
        self._root.title(string='fetch-yandex-news-gui')
        self._root.geometry('{}x{}'.format(
                DEFAULT_MAIN_WINDOW_WIDTH, DEFAULT_MAIN_WINDOW_HEIGHT))
        
        self._menubar = tkinter.Menu(master=self._root)
        self._program_menu = tkinter.Menu(master=self._menubar)
        self._program_menu.add_command(label='Select Source URLs File',
                command=self._select_source_urls_file_cmd)
        self._program_menu.add_command(label='Load / Reload', command=self._reload_cmd)
        self._program_menu.add_command(label='Copy', command=self._copy_cmd)
        self._program_menu.add_separator()
        self._program_menu.add_command(label='Close', command=self._close_cmd)
        self._menubar.add_cascade(label='Program', menu=self._program_menu)
        self._root.config(menu=self._menubar)
        
        self._top_frame = ttk.Frame(master=self._root)
        self._center_frame = ttk.Frame(master=self._root)
        self._bottom_frame = ttk.Frame(master=self._root)
        
        self._source_urls_file_label = ttk.Label(master=self._top_frame,
                text='Source URLs File:')
        self._source_urls_file_entry = ttk.Entry(master=self._top_frame)
        
        self._show_url_var = tkinter.BooleanVar()
        self._show_url = ttk.Checkbutton(
                master=self._top_frame, variable=self._show_url_var, text='Show URL')
        
        self._spec_url_sep_var = tkinter.BooleanVar()
        self._spec_url_sep = ttk.Checkbutton(
                master=self._top_frame, variable=self._spec_url_sep_var,
                text='Special URL Separator',
                )
        
        self._text = scrolledtext.ScrolledText(master=self._center_frame)
        self._text.propagate(False)
        self._text.config(state=tkinter.DISABLED)
        
        self._select_source_urls_file_button = ttk.Button(master=self._bottom_frame,
                text='Select Source URLs File',
                command=self._select_source_urls_file_cmd)
        self._reload_button = ttk.Button(master=self._bottom_frame,
                text='Load / Reload',
                command=self._reload_cmd)
        self._copy_button = ttk.Button(master=self._bottom_frame,
                text='Copy',
                command=self._copy_cmd)
        self._close_button = ttk.Button(master=self._bottom_frame,
                text='Close',
                command=self._close_cmd)
        
        self._status_var = tkinter.StringVar()
        self._statusbar = ttk.Label(master=self._bottom_frame,
                textvariable=self._status_var)
        
        self._source_urls_file_label.pack(side=tkinter.TOP, fill=tkinter.X, padx=10, pady=10)
        self._source_urls_file_entry.pack(side=tkinter.TOP, fill=tkinter.X, padx=10, pady=10)
        self._show_url.pack(side=tkinter.TOP, fill=tkinter.X, padx=10, pady=10)
        self._spec_url_sep.pack(side=tkinter.TOP, fill=tkinter.X, padx=10, pady=10)
        self._text.pack(fill=tkinter.BOTH, expand=True)
        self._select_source_urls_file_button.pack(side=tkinter.LEFT, padx=10, pady=10)
        self._reload_button.pack(side=tkinter.LEFT, padx=10, pady=10)
        self._copy_button.pack(side=tkinter.LEFT, padx=10, pady=10)
        self._statusbar.pack(side=tkinter.LEFT, expand=True, padx=10, pady=10)
        self._close_button.pack(side=tkinter.RIGHT, padx=10, pady=10)
        
        self._top_frame.pack(side=tkinter.TOP, fill=tkinter.X)
        self._center_frame.pack(fill=tkinter.BOTH, expand=True)
        self._bottom_frame.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        
        self._busy_state = False
        self._busy_state_id = object()
        self._set_status('Ready')
    
    def _close_cmd(self):
        if self._busy_state:
            self._root.bell()
            return
        
        self._tk_mt.push_destroy()
    
    def _set_status(self, text):
        self._status_var.set('Status: {}'.format(text))
    
    def _select_source_urls_file_result(self, busy_state_id, result):
        if self._busy_state or busy_state_id != self._busy_state_id:
            return
        
        if not result:
            return
        
        file_path = str(result)
        self._source_urls_file_entry.delete(0, tkinter.END)
        self._source_urls_file_entry.insert(0, file_path)
    
    def _select_source_urls_file_cmd(self):
        if self._busy_state:
            self._root.bell()
            return
        
        tk_async.tk_async(
                self._root,
                lambda: filedialog.askopenfilename(parent=self._root),
                self._busy_state_id,
                callback=self._select_source_urls_file_result,
                )
    
    def _reload_cmd(self):
        if self._busy_state:
            self._root.bell()
            return
        
        url_list_file_path = self._source_urls_file_entry.get().strip()
        show_url = self._show_url_var.get()
        spec_url_sep = self._spec_url_sep_var.get()
        
        if url_list_file_path:
            try:
                url_list = read_list.read_list(url_list_file_path)
            except EnvironmentError:
                # ``EnvironmentError`` will never excepted HERE,
                #   because ``read_list.read_list()`` -- is lazy generator
                
                self._root.bell()
                return
        else:
            url_list = None
        
        self._busy_state = True
        self._busy_state_id = object()
        self._set_status('Working')
        
        self._source_urls_file_entry.config(state=tkinter.DISABLED)
        self._show_url.config(state=tkinter.DISABLED)
        self._spec_url_sep.config(state=tkinter.DISABLED)
        self._select_source_urls_file_button.config(state=tkinter.DISABLED)
        self._reload_button.config(state=tkinter.DISABLED)
        self._copy_button.config(state=tkinter.DISABLED)
        self._close_button.config(state=tkinter.DISABLED)
        
        self._text.config(state=tkinter.NORMAL)
        self._text.delete('1.0', tkinter.END)
        self._text.config(state=tkinter.DISABLED)
        
        busy_state_id = self._busy_state_id
        
        def on_result(data):
            self._tk_mt.push(lambda: self._on_reload_result(
                    busy_state_id, show_url, spec_url_sep, data))
        
        def on_done():
            self._tk_mt.push(lambda: self._on_reload_done(busy_state_id))
        
        fetch_news.fetch_news(
                url_list=url_list,
                on_result=on_result,
                on_done=on_done,
                )
    
    def _on_reload_result(self, busy_state_id, show_url, spec_url_sep, data):
        if busy_state_id != self._busy_state_id:
            return
        
        if data.error is not None:
            return
        
        if spec_url_sep:
            url_separator = '|'
        else:
            url_separator = None
        
        self._text.config(state=tkinter.NORMAL)
        for result_line in fetch_news.result_line_format(
                data, show_url=show_url, url_separator=url_separator):
            self._text.insert(tkinter.END, '{}\n'.format(result_line))
        self._text.config(state=tkinter.DISABLED)
    
    def _on_reload_done(self, busy_state_id):
        if busy_state_id != self._busy_state_id:
            return
        
        self._busy_state = False
        self._busy_state_id = object()
        self._set_status('Done')
        
        self._source_urls_file_entry.config(state=tkinter.NORMAL)
        self._show_url.config(state=tkinter.NORMAL)
        self._spec_url_sep.config(state=tkinter.NORMAL)
        self._select_source_urls_file_button.config(state=tkinter.NORMAL)
        self._reload_button.config(state=tkinter.NORMAL)
        self._copy_button.config(state=tkinter.NORMAL)
        self._close_button.config(state=tkinter.NORMAL)
    
    def _copy_cmd(self):
        if self._busy_state:
            self._root.bell()
            return
        
        content = self._text.get('1.0', tkinter.END).rstrip()
        self._root.clipboard_clear()
        self._root.clipboard_append(content)
