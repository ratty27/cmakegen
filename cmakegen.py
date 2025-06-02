#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ======================================================================
#	CMake generator
# ======================================================================
import os
import sys
import json
import flet

# ----------------------------------------------------------------------
#	Constants
# ----------------------------------------------------------------------
SUPPORT_PLATFORMS = [
	"Windows",
	"MacOS",
	"Linux",
]

EXTENSIONS_CPP=[
	"c",
	"cc",
	"cpp",
	"cxx",
]

CXXSTANDARD= [
	"default",
	"C++11",
	"C++14",
	"C++17",
	"C++20"
]

PATHINFO_TYPE_NONE     = 0
PATHINFO_TYPE_ABSOLUTE = 1
PATHINFO_TYPE_RELATIVE = 2
PATHINFO_TYPE_ENV      = 3

LISTVIEW_TYPE_DIRS  = 0
LISTVIEW_TYPE_FILES = 1

FILENAME_CONFIG = "CMakeConfig.json"

# ----------------------------------------------------------------------
#	Variables
# ----------------------------------------------------------------------
current_solution = None
current_window = None

# ----------------------------------------------------------------------
def to_dict(obj):
	if isinstance(obj, dict):
		out = {}
		for key, val in obj.items():
			out[key] = to_dict(val)
		return out
	elif isinstance(obj, list):
		out = []
		for val in obj:
			out.append(to_dict(val))
		return out
	elif hasattr(obj, "__dict__"):
		temp = obj.__dict__
		out = {}
		for key, val in temp.items():
			out[key] = to_dict(val)
		return out
	else:
		return obj

# ----------------------------------------------------------------------
class path_info:
	"""Constructor"""
	def __init__(self, in_path = None, in_base=None):
		if in_path is not None:
			self.type = PATHINFO_TYPE_ABSOLUTE
			self.base_path = None
			self.path = in_path
			self.change_base_path(in_base)
		else:
			self.type = PATHINFO_TYPE_NONE
			self.base_path = None
			self.path = None
		self.platform = []

	def change_base_path(self, new_path):
		if self.type == PATHINFO_TYPE_RELATIVE:
			self.path = os.path.join(self.base_path, self.path)
			self.type = PATHINFO_TYPE_ABSOLUTE
			self.base_path = None
		if self.type == PATHINFO_TYPE_ABSOLUTE and new_path is not None:
			own_drive, own_path = os.path.splitdrive(self.path)
			chg_drive, chg_path = os.path.splitdrive(new_path)
			if own_drive == chg_drive:		
				self.type = PATHINFO_TYPE_RELATIVE
				self.base_path = new_path
				self.path = os.path.relpath(self.path, new_path)

	def set_platform(self, platname, enable):
		if enable:
			if platname not in self.platform:
				self.platform.append(platname)
		else:
			self.platform.removed(platname)

	@staticmethod
	def fromdict(s):
		if isinstance(s, list):
			out = []
			for elem in s:
				out.append(path_info.fromdict(elem))
			return out
		else:
			out = path_info()
			out.type = s['type']
			out.base_path = s['base_path']
			out.path = s['path']
			out.platform = s['platform']
			return out

# ----------------------------------------------------------------------
class project:
	"""Constructor"""
	def __init__(self):
		self.name = None
		self.include_dirs = []	# Array of path_info
		self.library_dirs = []
		self.sources = []
		self.platform = []
		self.stdcpp = CXXSTANDARD[0]

	def enable_platform(self, name, enable):
		if enable:
			if name not in self.platform:
				self.platform.append(name)
			self.add_plaform(name, self.include_dirs)
			self.add_plaform(name, self.library_dirs)
			self.add_plaform(name, self.sources)
		else:
			if name in self.platform:
				idx = self.platform.index(name)
				del self.platform[idx]
			self.del_plaform(name, self.include_dirs)
			self.del_plaform(name, self.library_dirs)
			self.del_plaform(name, self.sources)

	def add_plaform(self, name, pathlist):
		for info in pathlist:
			if name not in info.platform:
				info.platform.append(name)

	def del_plaform(self, name, pathlist):
		for info in pathlist:
			info.platform.remove(name)

	def change_base_path(self, old_path, new_path):
		self._change_base_path(self.include_dirs, old_path, new_path)
		self._change_base_path(self.library_dirs, old_path, new_path)
		self._change_base_path(self.sources, old_path, new_path)

	def _change_base_path(self, pathlist, old_path, new_path):
		for info in pathlist:
			info.change_base_path(new_path)

	@staticmethod
	def fromdict(s):
		out = project()
		out.name = s['name']
		out.include_dirs = path_info.fromdict(s['include_dirs'])
		out.library_dirs = path_info.fromdict(s['library_dirs'])
		out.sources = path_info.fromdict(s['sources'])
		out.platform = s['platform']
		out.stdcpp = s['stdcpp']
		return out

# ----------------------------------------------------------------------
class solution:
	"""Constructor"""
	def __init__(self):
		self.name = None
		self.path = None
		self.projects = []

	def add_project(self, proj):
		self.projects.append(proj)

	def new_project(self):
		proj = project()
		proj.name = "Project" + str(len(self.projects)+1)
		self.add_project(proj)
		return proj

	def set_path(self, in_path):
		for proj in self.projects:
			proj.change_base_path(self.path, in_path)
		self.path = in_path

	def get_savepath(self):
		return os.path.join(self.path, FILENAME_CONFIG)

	def save(self):
		data = to_dict(self)
		del data['path']
		#print(data)
		filepath = self.get_savepath()
		with open(filepath, 'w') as outfile:
			json.dump(data, outfile)
		return True

	def load(self, filepath):
		with open(filepath, 'r') as infile:
			data = json.load(infile)
		self.name = data['name']
		self.path = os.path.dirname(filepath)
		self.projects = []
		for sproj in data['projects']:
			proj = project.fromdict(sproj)
			self.projects.append(proj)



# ----------------------------------------------------------------------
##	Make columns list of flet.DataTable
#	@param	column_name		Array of column name string or control
def make_data_table_columuns(column_name):
	columns = []
	for name in column_name:
		if isinstance(name, str):
			ctrl = flet.DataColumn(flet.Text(name))
		else:
			ctrl = name
		columns.append( ctrl )
	return columns

# ----------------------------------------------------------------------
##	Make flet.DataTable
#	@param	column_name		Array of column name
def make_data_table(column_name,checkbox=False):
	columns = make_data_table_columuns(column_name)
	dt = flet.DataTable(columns=columns, show_checkbox_column=checkbox)
	return dt

# ----------------------------------------------------------------------
##	Add cells to flet.DataTable
#	@param	dt			DataTable
#	@param	columns		Array of controls
def add_data_table(dt, columns, idx, on_checked):
	cells = []
	for col in columns:
		a_cell = flet.DataCell(col)
		cells.append(a_cell)
	row = flet.DataRow(cells=cells, selected=False, on_select_changed=on_checked)
	row.idx = idx
	dt.rows.append(row)

# ----------------------------------------------------------------------
##	ListView of pathes
class listview_path:
	"""Constructor"""
	def __init__(self, in_type, in_owner, proj, in_list_path):
		self.type = in_type
		self.project = proj
		self.owner = in_owner
		self.dt = None
		self.list_path = in_list_path	# ! Direct referefence to the path list

	def build(self, parent, title):
		parent.controls.append(flet.Text(title, weight=flet.FontWeight.BOLD))
		names = []
		names.append("Path")
		for platname in SUPPORT_PLATFORMS:
			if platname in self.project.platform:
				names.append(platname)
		self.dt = make_data_table(names, True)
		self.update_list(False)
		box = flet.Container(content=self.dt)
		box.border = flet.border.all(2, "#303030")
		parent.controls.append(box)
		# buttons
		addbtn = flet.FilledButton("Add", on_click=self.on_press_add_path)
		delbtn = flet.FilledButton("Delete Checked", on_click=self.on_press_del_path)
		box = flet.Row(spacing=8, controls=[addbtn, delbtn])
		parent.controls.append(box)

	def update_list(self, update_immediately=True):
		names = []
		names.append("Path")
		for platname in SUPPORT_PLATFORMS:
			if platname in self.project.platform:
				names.append(platname)
		self.dt.columns = make_data_table_columuns(names) 
		self.dt.rows.clear()
		idx = 0
		for item in self.list_path:
			text = flet.Text(item.path)
			clmns = [text]
			for platname in SUPPORT_PLATFORMS:
				if platname in self.project.platform:
					if platname in item.platform:
						init = True
					else:
						init = False
					chk = flet.Checkbox(value=init, on_change=self.on_platform_choosed)
					chk.platform = platname
					chk.idx = idx
					clmns.append(chk)
			add_data_table(self.dt, clmns, idx, self.on_selection_changed)
			idx += 1
		if update_immediately:
			self.dt.update()
			#self.owner.page.update()

	def on_press_add_path(self, e):
		init_path = self.owner.get_solution_path()
		if init_path is None:
			init_path = self.owner.get_init_path()
		if self.type == LISTVIEW_TYPE_DIRS:
			self.owner.choose_a_dir("Choose path", init_path, self.on_path_selected)
		elif self.type == LISTVIEW_TYPE_FILES:
			self.owner.choose_a_file("Choose file", init_path, self.on_path_selected)

	def on_path_selected(self, path):
		base_path = self.owner.get_solution_path()
		info = path_info(path, base_path)
		#print(path + ' / ' + base_path )
		info.platform = self.project.platform.copy()
		self.list_path.append(info)
		self.update_list(True)

	def on_selection_changed(self, e):
		e.control.selected = e.data
		e.control.update()

	def on_press_del_path(self, e):
		selected  = []
		for row in self.dt.rows:
			if row.selected:
				selected.append(row.idx)
		for idx in reversed(selected):
			if idx < len(self.list_path):
				del self.list_path[idx]
		self.update_list(True)

	def on_platform_choosed(self, e):
		idx = e.control.idx
		platname = e.control.platform
		if idx < len(self.list_path):
			self.list_path[idx].set_platform(platname, e.data)

# ----------------------------------------------------------------------
##	Project tab
class project_tab:
	"""Constructor"""
	def __init__(self, in_owner, proj):
		self.project = proj
		self.chk_platform = []
		self.owner = in_owner

	"""On change project name"""
	def on_change_project_name(self, e):
		self.project.name = e.control.value

	"""On click Platform"""
	def on_change_plaform(self, e):
		self.project.enable_platform(e.control.label, e.control.value)
		self.lv_include_dirs.update_list(True)
		self.lv_library_dirs.update_list(True)
		self.lv_source_files.update_list(True)

	"""On change c++ stadard"""
	def on_change_cpp_standard(self, e):
		self.project.stdcpp = e.control.value

	def on_basepath_changed(self):
		self.lv_include_dirs.update_list(False)
		self.lv_library_dirs.update_list(False)
		self.lv_source_files.update_list(True)


	def build(self):
		# Name
		content = flet.TextField(label="Project name", on_change=self.on_change_project_name, value=self.project.name, border_color="#808080")
		# - Panel
		title = flet.Text(" Project", weight=flet.FontWeight.BOLD, size=32)
		panel_project = flet.ExpansionPanel(header=title, can_tap_header=True, expanded=True, bgcolor="#4a4f62")
		panel_project.content = content

		# Platform
		content = flet.Row()
		# - Plateform checkbox
		self.chk_platform = []
		idx = 0
		while idx < len(SUPPORT_PLATFORMS):
			if SUPPORT_PLATFORMS[idx] in self.project.platform:
				support = True
			else:
				support = False
			chk = flet.Checkbox(label=SUPPORT_PLATFORMS[idx], value=support, on_change=self.on_change_plaform)
			self.chk_platform.append(chk)
			content.controls.append(chk)
			idx += 1
		# - Panel
		title = flet.Text(" Platform", weight=flet.FontWeight.BOLD, size=32)
		panel_platform = flet.ExpansionPanel(header=title, can_tap_header=True, expanded=True, bgcolor="#4a4f62")
		panel_platform.content = content

		# C/C++
		content = flet.Column()
		# - C++ standard
		content.controls.append(flet.Text("C++ standard", weight=flet.FontWeight.BOLD))
		opt = []
		for item in CXXSTANDARD:
			opt.append(flet.dropdown.Option(item))
		dd = flet.Dropdown(options=opt, on_change=self.on_change_cpp_standard)
		dd.value = self.project.stdcpp
		content.controls.append(dd)
		# - include directories
		self.lv_include_dirs = listview_path(LISTVIEW_TYPE_DIRS, self.owner, self.project, self.project.include_dirs)
		self.lv_include_dirs.build(content, "Include directories")
		# - library directories
		self.lv_library_dirs = listview_path(LISTVIEW_TYPE_DIRS, self.owner, self.project, self.project.library_dirs)
		self.lv_library_dirs.build(content, "Library directories")
		# - Sounrce Files
		self.lv_source_files = listview_path(LISTVIEW_TYPE_FILES, self.owner, self.project, self.project.sources)
		self.lv_source_files.build(content, "Sounrce Files")
		# - Panel
		title = flet.Text(" C/C++", weight=flet.FontWeight.BOLD, size=32)
		panel_cpp = flet.ExpansionPanel(header=title, can_tap_header=True, expanded=True, bgcolor="#4a4f62")
		panel_cpp.content = content

		#
		self.content = flet.ExpansionPanelList(controls=[panel_project, panel_platform, panel_cpp])
		#

		return self.content

# ----------------------------------------------------------------------
##	Window
class window:
	"""Constructor"""
	def __init__(self, in_sln):
		self.solution = in_sln
		self.tab_projects = None
		self.content_projects = []
		self.page = None
		self.cb_choose_path = None

	def __on_click_tab(self, e):
		idx = int(e.data)
		if idx == len(self.tab_projects.tabs)-1:
			# Add new project
			proj = self.solution.new_project()
			projtab, tab = self.__build_project_tab(proj)
			self.tab_projects.tabs.insert(len(self.tab_projects.tabs)-1, tab)
			self.content_projects.append(projtab)
			self.page.update()

	"""Build a project tab"""
	def __build_project_tab(self, proj):
		projtab = project_tab(self, proj)
		content = projtab.build()
		tab = flet.Tab(text=proj.name, content=content)
		return projtab, tab

	"""Result of choose path"""
	def __on_path_choosed(self, e):
		if self.cb_choose_path is not None:
			if e.path is not None:
				self.cb_choose_path(e.path)
			elif e.files is not None:
				for fileinfo in e.files:
					self.cb_choose_path(fileinfo.path)
			self.cb_choose_path = None
			return
		self.solution.set_path( e.path )
		self.ctrl_solution_path.value = e.path
		for tab in self.content_projects:
			tab.on_basepath_changed()
		self.page.update()

	def get_init_path(self):
		if self.solution.path is None:
			return os.path.expanduser("~")
		else:
			return self.solution.path


	"""Choose path"""
	def on_press_choose_path(self, e):
		path_init = self.get_init_path()
		self.choose_file.get_directory_path(dialog_title="Choose path to solution root", initial_directory=path_init)

	"""Choose a directory"""
	def choose_a_dir(self, title, initial_path, cb):
		self.cb_choose_path = cb
		self.choose_file.get_directory_path(dialog_title=title, initial_directory=initial_path)

	def choose_a_file(self, title, initial_path, cb):
		self.cb_choose_path = cb
		self.choose_file.pick_files(dialog_title=title, initial_directory=initial_path, file_type=flet.FilePickerFileType.CUSTOM, allowed_extensions=EXTENSIONS_CPP, allow_multiple=False)

	def get_solution_path(self):
		return self.solution.path

	def open_info_dialog(self, title, message):
		self.dlg_info.title.value=title
		self.dlg_info.content.value=message
		self.page.open(self.dlg_info)

	def on_close_info_dialog(self, e):
		self.page.close(self.dlg_info)

	"""Build window"""
	def build(self, in_page):
		self.page = in_page
		self.page.scroll = flet.ScrollMode.AUTO
		self.page.bgcolor = "#27282b"
		# info dialog
		self.dlg_info = flet.AlertDialog(
			title=flet.Text("title"),
			content=flet.Text("message"),
			actions=[
				flet.TextButton("Ok", on_click=self.on_close_info_dialog),
			],
		)
		# Prepare file picker
		self.choose_file = flet.FilePicker(on_result=self.__on_path_choosed)
		self.page.overlay.append(self.choose_file)
		# Solution
		# - Name
		def on_change_solution_name(e):
			self.solution.name = e.control.value
		row = flet.Row(
			[
				flet.TextField(label="Solution name", on_change=on_change_solution_name, value=self.solution.name, border_color="#808080"),
				flet.FilledButton("Save", on_click=self.on_press_save_solution),
				flet.FilledButton("Load", on_click=self.on_press_load_solution)
			]
		)
		self.page.add( row )
		# - Path
		self.ctrl_solution_path = flet.TextField(label="Path", width=600, on_change=on_change_solution_name, value=self.solution.name, border_color="#808080")
		row = flet.Row(
			[
				self.ctrl_solution_path,
				flet.FilledButton("...", on_click=self.on_press_choose_path)
			]
		)
		self.page.add( row )
		# Projects
		self.tab_projects = flet.Tabs(on_click=self.__on_click_tab)
		for proj in self.solution.projects:
			projtab, tab = self.__build_project_tab(proj)
			self.tab_projects.tabs.append(tab)
			self.content_projects.append(projtab)
		tab = flet.Tab(text="+NewProject")
		self.tab_projects.tabs.append(tab)
		self.page.add(self.tab_projects)

	def on_press_save_solution(self, e):
		if self.solution.path is None:
			self.open_info_dialog("Error", 'Solution path must be not empty')
		if not os.path.isdir(self.solution.path):
			self.open_info_dialog("Error", 'Solution path is incorrect')
		if not self.solution.save():
			self.open_info_dialog("Error", 'Failed to save solution')

	def on_press_load_solution(self, e):
		pass
		#self.solution.load(s)

# ----------------------------------------------------------------------
def main(page: flet.Page):
	page.title = "cmakegen"
	current_window.build(page)
	page.update()

current_solution = solution()
if len(sys.argv) >= 2:
	filename = sys.argv[1]
	if os.path.isfile(filename):
		current_solution.load(filename)
	else:
		sys.stdout.write('Error: File not found: ' + filename)
current_window = window(current_solution)
flet.app(target=main)
