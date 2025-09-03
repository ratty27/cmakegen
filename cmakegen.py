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
#	Modern UI Constants
# ----------------------------------------------------------------------
COLORS = {
	"primary": "#6366f1",
	"primary_dark": "#4f46e5",
	"secondary": "#8b5cf6",
	"accent": "#06b6d4",
	"success": "#10b981",
	"warning": "#f59e0b",
	"error": "#ef4444",
	"background": "#0f172a",
	"surface": "#1e293b",
	"surface_light": "#334155",
	"text_primary": "#f8fafc",
	"text_secondary": "#cbd5e1",
	"border": "#475569",
	"border_light": "#64748b"
}

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
			if platname in self.platform:
				self.platform.remove(platname)

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
		self.name = "Project1"  # Set default name
		self.include_dirs = []	# Array of path_info
		self.library_dirs = []
		self.sources = []
		self.platform = ["Windows"]  # Default to Windows platform
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
			if name in info.platform:
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
		print(f"Created project: {proj.name} with platforms: {proj.platform}")
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

	def generate_cmake(self):
		"""Generate CMakeLists.txt file"""
		if not self.path or not os.path.isdir(self.path):
			return False, "Solution path is not set or invalid"
		
		cmake_content = []
		cmake_content.append(f"cmake_minimum_required(VERSION 3.10)")
		cmake_content.append(f"project({self.name})")
		cmake_content.append("")
		
		# Set C++ standard
		for proj in self.projects:
			if proj.stdcpp != "default":
				std_version = proj.stdcpp.replace("C++", "")
				cmake_content.append(f"set(CMAKE_CXX_STANDARD {std_version})")
				cmake_content.append(f"set(CMAKE_CXX_STANDARD_REQUIRED ON)")
				break
		
		cmake_content.append("")
		
		# Generate for each project
		for proj in self.projects:
			cmake_content.append(f"# Project: {proj.name}")
			
			# Add executable
			cmake_content.append(f"add_executable({proj.name}")
			
			# Add source files
			for source in proj.sources:
				if source.path:
					cmake_content.append(f"    {source.path}")
			cmake_content.append(")")
			cmake_content.append("")
			
			# Add include directories
			if proj.include_dirs:
				cmake_content.append(f"target_include_directories({proj.name} PRIVATE")
				for include_dir in proj.include_dirs:
					if include_dir.path:
						cmake_content.append(f"    {include_dir.path}")
				cmake_content.append(")")
				cmake_content.append("")
			
			# Add library directories
			if proj.library_dirs:
				cmake_content.append(f"target_link_directories({proj.name} PRIVATE")
				for lib_dir in proj.library_dirs:
					if lib_dir.path:
						cmake_content.append(f"    {lib_dir.path}")
				cmake_content.append(")")
				cmake_content.append("")
		
		# Write CMakeLists.txt
		cmake_file = os.path.join(self.path, "CMakeLists.txt")
		try:
			with open(cmake_file, 'w', encoding='utf-8') as f:
				f.write('\n'.join(cmake_content))
			return True, f"CMakeLists.txt generated successfully at {cmake_file}"
		except Exception as e:
			return False, f"Failed to generate CMakeLists.txt: {str(e)}"



# ----------------------------------------------------------------------
##	Make columns list of flet.DataTable
#	@param	column_name		Array of column name string or control
def make_data_table_columuns(column_name):
	columns = []
	for name in column_name:
		if isinstance(name, str):
			ctrl = flet.DataColumn(flet.Text(name, color=COLORS["text_primary"], weight=flet.FontWeight.W_600))
		else:
			ctrl = name
		columns.append( ctrl )
	return columns

# ----------------------------------------------------------------------
##	Make flet.DataTable
#	@param	column_name		Array of column name
def make_data_table(column_name,checkbox=False):
	columns = make_data_table_columuns(column_name)
	dt = flet.DataTable(
		columns=columns, 
		show_checkbox_column=checkbox,
		border=flet.border.all(1, COLORS["border"]),
		border_radius=8,
		heading_row_color=COLORS["surface_light"],
		heading_text_style=flet.TextStyle(color=COLORS["text_primary"], weight=flet.FontWeight.W_600),
		data_row_color={"hovered": COLORS["surface_light"]},
		divider_thickness=1,
		column_spacing=20
	)
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
		# Title with icon
		title_row = flet.Row([
			flet.Icon(
				name="folder" if self.type == LISTVIEW_TYPE_DIRS else "description",
				color=COLORS["accent"],
				size=24
			),
			flet.Text(title, weight=flet.FontWeight.BOLD, size=18, color=COLORS["text_primary"])
		], spacing=12)
		parent.controls.append(title_row)
		
		names = []
		names.append("Path")
		for platname in SUPPORT_PLATFORMS:
			if platname in self.project.platform:
				names.append(platname)
		self.dt = make_data_table(names, True)
		self.update_list(False)
		
		# Card container for table
		table_card = flet.Container(
			content=self.dt,
			padding=16,
			bgcolor=COLORS["surface"],
			border_radius=12,
			border=flet.border.all(1, COLORS["border"]),
			shadow=flet.BoxShadow(
				spread_radius=1,
				blur_radius=15,
				color=COLORS["background"],
				offset=flet.Offset(0, 4)
			)
		)
		parent.controls.append(table_card)
		
		# Modern buttons
		addbtn = flet.ElevatedButton(
			"Add",
			icon=flet.Icon("add", color=COLORS["success"]),
			on_click=self.on_press_add_path,
			bgcolor=COLORS["success"],
			color=COLORS["text_primary"],
			style=flet.ButtonStyle(
				shape=flet.RoundedRectangleBorder(radius=8),
				padding=12
			)
		)
		delbtn = flet.ElevatedButton(
			"Delete Checked",
			icon=flet.Icon("delete", color=COLORS["error"]),
			on_click=self.on_press_del_path,
			bgcolor=COLORS["error"],
			color=COLORS["text_primary"],
			style=flet.ButtonStyle(
				shape=flet.RoundedRectangleBorder(radius=8),
				padding=12
			)
		)
		button_row = flet.Row(spacing=12, controls=[addbtn, delbtn])
		parent.controls.append(button_row)
		
		# Add spacing
		parent.controls.append(flet.Container(height=20))

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
			text = flet.Text(item.path, color=COLORS["text_secondary"])
			clmns = [text]
			for platname in SUPPORT_PLATFORMS:
				if platname in self.project.platform:
					if platname in item.platform:
						init = True
					else:
						init = False
					chk = flet.Checkbox(
						value=init, 
						on_change=self.on_platform_choosed,
						fill_color=COLORS["primary"],
						check_color=COLORS["text_primary"]
					)
					chk.platform = platname
					chk.idx = idx
					clmns.append(chk)
			add_data_table(self.dt, clmns, idx, self.on_selection_changed)
			idx += 1
		if update_immediately:
			self.dt.update()

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
		print(f"Building project tab content for: {self.project.name}")
		
		# Ensure project has valid data
		if self.project.name is None:
			self.project.name = "Project1"
		if not self.project.platform:
			self.project.platform = ["Windows"]
		if self.project.stdcpp is None:
			self.project.stdcpp = CXXSTANDARD[0]
		
		print(f"   - Project initialized: {self.project.name}")
		print(f"   - Platforms: {self.project.platform}")
		print(f"   - C++ standard: {self.project.stdcpp}")
		
		# Project Name Panel
		name_content = flet.TextField(
			label="Project name", 
			on_change=self.on_change_project_name, 
			value=self.project.name, 
			border_color=COLORS["border"],
			focused_border_color=COLORS["primary"],
			label_style=flet.TextStyle(color=COLORS["text_secondary"]),
			text_style=flet.TextStyle(color=COLORS["text_primary"]),
			bgcolor=COLORS["surface_light"],
			border_radius=8
		)
		
		title = flet.Row([
			flet.Icon("build", color=COLORS["primary"], size=28),
			flet.Text(" Project", weight=flet.FontWeight.BOLD, size=24, color=COLORS["text_primary"])
		], spacing=12)
		
		panel_project = flet.ExpansionPanel(
			header=title, 
			can_tap_header=True, 
			expanded=True, 
			bgcolor=COLORS["surface"],
			content=flet.Container(
				content=name_content,
				padding=20,
				bgcolor=COLORS["surface_light"],
				border_radius=8
			)
		)

		# Platform Panel
		platform_content = flet.Row(spacing=16)
		self.chk_platform = []
		idx = 0
		while idx < len(SUPPORT_PLATFORMS):
			if SUPPORT_PLATFORMS[idx] in self.project.platform:
				support = True
			else:
				support = False
			chk = flet.Checkbox(
				label=SUPPORT_PLATFORMS[idx], 
				value=support, 
				on_change=self.on_change_plaform,
				fill_color=COLORS["primary"],
				check_color=COLORS["text_primary"],
				label_style=flet.TextStyle(color=COLORS["text_primary"])
			)
			self.chk_platform.append(chk)
			platform_content.controls.append(chk)
			idx += 1
		
		platform_title = flet.Row([
			flet.Icon("computer", color=COLORS["secondary"], size=28),
			flet.Text(" Platform", weight=flet.FontWeight.BOLD, size=24, color=COLORS["text_primary"])
		], spacing=12)
		
		panel_platform = flet.ExpansionPanel(
			header=platform_title, 
			can_tap_header=True, 
			expanded=True, 
			bgcolor=COLORS["surface"],
			content=flet.Container(
				content=platform_content,
				padding=20,
				bgcolor=COLORS["surface_light"],
				border_radius=8
			)
		)

		# C/C++ Panel
		cpp_content = flet.Column(spacing=16)
		
		# C++ standard
		cpp_content.controls.append(flet.Text("C++ standard", weight=flet.FontWeight.BOLD, color=COLORS["text_primary"]))
		opt = []
		for item in CXXSTANDARD:
			opt.append(flet.dropdown.Option(item))
		dd = flet.Dropdown(
			options=opt, 
			on_change=self.on_change_cpp_standard,
			border_color=COLORS["border"],
			focused_border_color=COLORS["primary"],
			bgcolor=COLORS["surface_light"],
			color=COLORS["text_primary"]
		)
		dd.value = self.project.stdcpp
		cpp_content.controls.append(dd)
		
		# Add spacing after dropdown
		cpp_content.controls.append(flet.Container(height=16))
		
		# include directories
		self.lv_include_dirs = listview_path(LISTVIEW_TYPE_DIRS, self.owner, self.project, self.project.include_dirs)
		self.lv_include_dirs.build(cpp_content, "Include directories")
		
		# library directories
		self.lv_library_dirs = listview_path(LISTVIEW_TYPE_DIRS, self.owner, self.project, self.project.library_dirs)
		self.lv_library_dirs.build(cpp_content, "Library directories")
		
		# Source Files
		self.lv_source_files = listview_path(LISTVIEW_TYPE_FILES, self.owner, self.project, self.project.sources)
		self.lv_source_files.build(cpp_content, "Source Files")
		
		cpp_title = flet.Row([
			flet.Icon("code", color=COLORS["accent"], size=28),
			flet.Text(" C/C++", weight=flet.FontWeight.BOLD, size=24, color=COLORS["text_primary"])
		], spacing=12)
		
		panel_cpp = flet.ExpansionPanel(
			header=cpp_title, 
			can_tap_header=True, 
			expanded=True, 
			bgcolor=COLORS["surface"],
			content=flet.Container(
				content=cpp_content,
				padding=20,
				bgcolor=COLORS["surface_light"],
				border_radius=8
			)
		)

		# Create expansion panel list with modern styling
		print(f"Creating ExpansionPanelList with {len([panel_project, panel_platform, panel_cpp])} panels")
		self.content = flet.ExpansionPanelList(
			controls=[panel_project, panel_platform, panel_cpp],
			spacing=16,
			elevation=8,
			expand_icon_color=COLORS["primary"]
		)
		print(f"ExpansionPanelList created: {self.content}")
		
		# Debug: Print the content structure
		print(f"✅ Project tab content built successfully for {self.project.name}")
		print(f"   - Project name: {self.project.name}")
		print(f"   - Platforms: {self.project.platform}")
		print(f"   - C++ standard: {self.project.stdcpp}")
		print(f"   - Include dirs count: {len(self.project.include_dirs)}")
		print(f"   - Library dirs count: {len(self.project.library_dirs)}")
		print(f"   - Sources count: {len(self.project.sources)}")
		print(f"   - Content type: {type(self.content)}")
		print(f"   - Content controls count: {len(self.content.controls)}")

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
			
			# Set the newly created tab as selected
			self.tab_projects.selected_index = len(self.tab_projects.tabs) - 2
			
			# Force update of the entire page to ensure UI consistency
			self.page.update()
			# Also update the tabs container specifically
			if hasattr(self, 'tabs_card'):
				self.tabs_card.update()

	"""Build a project tab"""
	def __build_project_tab(self, proj):
		print(f"Building project tab for: {proj.name}")
		projtab = project_tab(self, proj)
		content = projtab.build()
		print(f"Content built successfully for {proj.name}")
		print(f"   - Content type: {type(content)}")
		print(f"   - Content has controls: {hasattr(content, 'controls')}")
		if hasattr(content, 'controls'):
			print(f"   - Content controls count: {len(content.controls)}")
		
		tab = flet.Tab(
			text=proj.name, 
			content=content,
			icon=flet.Icon("folder", color=COLORS["accent"])
		)
		print(f"Tab created for {proj.name}: {tab}")
		print(f"   - Tab content: {tab.content}")
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
		self.page.scroll = flet.ScrollMode.ALWAYS
		self.page.bgcolor = COLORS["background"]
		self.page.padding = 24
		self.page.spacing = 20
		
		# Header with gradient background
		header = flet.Container(
			content=flet.Column([
				flet.Row([
					flet.Icon("construction", color=COLORS["primary"], size=32),
					flet.Text("CMake Generator", size=32, weight=flet.FontWeight.BOLD, color=COLORS["text_primary"])
				], spacing=16),
				flet.Text("Professional CMake project configuration tool", size=16, color=COLORS["text_secondary"])
			]),
			padding=24,
			bgcolor=COLORS["surface"],
			border_radius=16,
			border=flet.border.all(1, COLORS["border"]),
			shadow=flet.BoxShadow(
				spread_radius=1,
				blur_radius=20,
				color=COLORS["background"],
				offset=flet.Offset(0, 8)
			)
		)
		self.page.add(header)
		
		# info dialog
		self.dlg_info = flet.AlertDialog(
			title=flet.Text("title", color=COLORS["text_primary"]),
			content=flet.Text("message", color=COLORS["text_secondary"]),
			bgcolor=COLORS["surface"],
			actions=[
				flet.TextButton("Ok", on_click=self.on_close_info_dialog, style=flet.ButtonStyle(color=COLORS["primary"])),
			],
		)
		
		# Prepare file picker
		self.choose_file = flet.FilePicker(on_result=self.__on_path_choosed)
		self.page.overlay.append(self.choose_file)
		
		# Solution Configuration Card
		solution_card = flet.Container(
			content=flet.Column([
				# Solution Name Row
				flet.Row([
					flet.TextField(
						label="Solution name", 
						on_change=lambda e: setattr(self.solution, 'name', e.control.value), 
						value=self.solution.name, 
						border_color=COLORS["border"],
						focused_border_color=COLORS["primary"],
						label_style=flet.TextStyle(color=COLORS["text_secondary"]),
						text_style=flet.TextStyle(color=COLORS["text_primary"]),
						bgcolor=COLORS["surface_light"],
						border_radius=8,
						expand=True
					),
					flet.ElevatedButton(
						"Save",
						icon=flet.Icon("save", color=COLORS["text_primary"]),
						on_click=self.on_press_save_solution,
						bgcolor=COLORS["primary"],
						color=COLORS["text_primary"],
						style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=8), padding=12)
					),
					flet.ElevatedButton(
						"Load",
						icon=flet.Icon("folder_open", color=COLORS["text_primary"]),
						on_click=self.on_press_load_solution,
						bgcolor=COLORS["secondary"],
						color=COLORS["text_primary"],
						style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=8), padding=12)
					),
					flet.ElevatedButton(
						"Generate",
						icon=flet.Icon("play_arrow", color=COLORS["text_primary"]),
						on_click=self.on_press_generate_cmake,
						bgcolor=COLORS["success"],
						color=COLORS["text_primary"],
						style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=8), padding=12)
					)
				], spacing=12),
				
				# Solution Path Row
				flet.Row([
					flet.TextField(
						label="Path", 
						width=600, 
						on_change=lambda e: setattr(self.solution, 'path', e.control.value), 
						value=self.solution.path, 
						border_color=COLORS["border"],
						focused_border_color=COLORS["primary"],
						label_style=flet.TextStyle(color=COLORS["text_secondary"]),
						text_style=flet.TextStyle(color=COLORS["text_primary"]),
						bgcolor=COLORS["surface_light"],
						border_radius=8
					),
					flet.ElevatedButton(
						"...",
						on_click=self.on_press_choose_path,
						bgcolor=COLORS["surface_light"],
						color=COLORS["text_primary"],
						style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=8), padding=12)
					)
				], spacing=12)
			], spacing=16),
			padding=24,
			bgcolor=COLORS["surface"],
			border_radius=16,
			border=flet.border.all(1, COLORS["border"]),
			shadow=flet.BoxShadow(
				spread_radius=1,
				blur_radius=15,
				color=COLORS["background"],
				offset=flet.Offset(0, 4)
			)
		)
		self.page.add(solution_card)
		
		# Projects Section
		projects_header = flet.Container(
			content=flet.Row([
				flet.Icon("apps", color=COLORS["accent"], size=28),
				flet.Text("Projects", size=24, weight=flet.FontWeight.BOLD, color=COLORS["text_primary"])
			], spacing=12),
			padding=16,
			bgcolor=COLORS["surface"],
			border_radius=12,
			border=flet.border.all(1, COLORS["border"])
		)
		self.page.add(projects_header)
		
		# Projects Tabs
		self.tab_projects = flet.Tabs(
			on_click=self.__on_click_tab,
			selected_index=0,
			animation_duration=300,
			indicator_color=COLORS["primary"],
			label_color=COLORS["text_primary"],
			unselected_label_color=COLORS["text_secondary"],
			visible=True,
			height=600
		)
		
		# Add default project if none exists
		if len(self.solution.projects) == 0:
			default_proj = self.solution.new_project()
			projtab, tab = self.__build_project_tab(default_proj)
			print(f"Adding tab to tab_projects: {tab}")
			self.tab_projects.tabs.append(tab)
			self.content_projects.append(projtab)
			print(f"Created default project: {default_proj.name}")
			print(f"Tab_projects.tabs length after adding: {len(self.tab_projects.tabs)}")
		else:
			for proj in self.solution.projects:
				projtab, tab = self.__build_project_tab(proj)
				self.tab_projects.tabs.append(tab)
				self.content_projects.append(projtab)
		
		# Add new project tab
		print("Creating + New Project tab")
		new_tab = flet.Tab(
			text="+ New Project",
			icon=flet.Icon("add_circle", color=COLORS["success"]),
			content=flet.Container(
				content=flet.Column([
					flet.Icon("add_circle", color=COLORS["success"], size=64),
					flet.Text("Click to create a new project", 
						size=18, 
						color=COLORS["text_secondary"],
						text_align=flet.TextAlign.CENTER
					)
				], 
				horizontal_alignment=flet.CrossAxisAlignment.CENTER,
				spacing=20),
				padding=40,
				alignment=flet.alignment.center
			)
		)
		print(f"New project tab created: {new_tab}")
		print(f"New project tab content: {new_tab.content}")
		self.tab_projects.tabs.append(new_tab)
		print(f"New project tab added to tab_projects")
		print(f"Total tabs created: {len(self.tab_projects.tabs)}")
		print(f"Projects in solution: {len(self.solution.projects)}")
		
		# Force select the first tab
		self.tab_projects.selected_index = 0
		print(f"✅ Created {len(self.tab_projects.tabs)} tabs, selected index: {self.tab_projects.selected_index}")
		
		# Wrap tabs in a card and save as instance variable
		print(f"Creating tabs_card container with {len(self.tab_projects.tabs)} tabs")
		self.tabs_card = flet.Container(
			content=self.tab_projects,
			padding=20,
			bgcolor=COLORS["surface"],
			border_radius=16,
			border=flet.border.all(1, COLORS["border"]),
			shadow=flet.BoxShadow(
				spread_radius=1,
				blur_radius=15,
				color=COLORS["background"],
				offset=flet.Offset(0, 4)
			),
			visible=True,
			height=650
		)
		self.page.add(self.tabs_card)
		
		# Update UI to ensure tabs are displayed
		print(f"🔧 Updating UI components...")
		self.tab_projects.update()
		self.page.update()
		
		# Final verification
		print(f"✅ Final verification:")
		print(f"   - Tab projects visible: {self.tab_projects.visible}")
		print(f"   - Tabs card visible: {self.tabs_card.visible}")
		print(f"   - Tab projects height: {getattr(self.tab_projects, 'height', 'Not set')}")
		print(f"   - Tabs card height: {getattr(self.tabs_card, 'height', 'Not set')}")
		print(f"   - Total tabs: {len(self.tab_projects.tabs)}")
		print(f"   - Selected index: {self.tab_projects.selected_index}")
		print(f"✅ Tabs added to page and UI updated!")

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

	def on_press_generate_cmake(self, e):
		"""Generate CMakeLists.txt when Generate button is clicked"""
		success, message = self.solution.generate_cmake()
		if success:
			self.open_info_dialog("Success", message)
		else:
			self.open_info_dialog("Error", message)

# ----------------------------------------------------------------------
def main(page: flet.Page):
	page.title = "CMake Generator"
	page.theme_mode = flet.ThemeMode.DARK
	page.window.width = 1400
	page.window.height = 900
	page.window.resizable = True
	page.window.maximizable = True
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
