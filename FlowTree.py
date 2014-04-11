import sublime, sublime_plugin
import os
from collections import defaultdict

class FlowNode(object):
	def __init__(self, description, children, is_search, is_open, view):
		self.description = description
		self.children = children
		self.is_search = is_search
		self.is_open = is_open
		self.was_modified = False
		self.view = view

class FlowTreeCommand(sublime_plugin.WindowCommand):
	root_node = FlowNode(None, [], False, True, None)
	node_hist = [root_node]
	node_index = {}
	searches_in_view = defaultdict(list)
	@classmethod
	def summarize_selections(cls, view):
		sels = view.sel()
		if len(sels) > 1:
			return "Multiple blocks of text left selected"
		sel = view.substr(sels[0])
		if len(sel) > 50:
			return "Over 50 characters of text left selected"
		elif sel:
			return "Text left selected: " + repr(bytes(sel))
		else:
			return None
	@classmethod
	def visit_node(cls, view, is_search=False):
		if is_search:
			last_search = view.find_all('Searching \d+ files for .*$')[-1]
			desc = view.substr(last_search)
			vid = str(view.id()) + '-' + desc
		else:
			desc = os.path.basename(view.file_name()) + ' (' + view.file_name() + ')'
			vid = str(view.id())

		if vid in cls.node_index:
			cls.node_hist.append(cls.node_index[vid])
		else:
			new_node = FlowNode(desc, [], is_search, True, view)
			# Filter out nodes that have been closed; they can't be assigned parentage.
			# (Mostly for the sake of searches.)
			cls.node_hist = [node for node in cls.node_hist if node.is_open]
			# Search views look for the most recent non-search view to use as their parent.
			# That's because when you make a search, if you had made any searches previously,
			# the latest of those searches will be registered in the node history
			# before you make your new search.  So without this your previous search would
			# always be the parent of your new search.
			hist = [node for node in cls.node_hist if not node.is_search] if is_search else cls.node_hist
			hist[-1].children.append(new_node)
			cls.node_index[vid] = new_node
			cls.node_hist.append(new_node)
		if len(cls.node_hist) > 100:
			cls.node_hist = cls.node_hist[-50:]
	@classmethod
	def on_activated(cls, view):
		if view.file_name():
			cls.visit_node(view)
	@classmethod
	def on_post_save(cls, view):
		# This if should always be True but maybe there's something I don't know.
		if view.file_name():
			cls.visit_node(view)
	@classmethod
	def on_deactivated(cls, view):
		if 'Find Results' in view.name():
			cls.visit_node(view, True)
	@classmethod
	def flow_tree(cls):
		def show_node(node, indent):
			result = '  ' * indent
			# Checked box for closed files; unchecked box for open files.
			if node.is_search:
				result += u'? '
			else:
				result += u'\u2610 ' if node.is_open else u'\u2611 '
			result += node.description
			result += '\n'
			if node.was_modified:
				result += '  ' * (indent + 1)
				result += 'Made modifications to this file'
				result += '\n'
			selections_summary = cls.summarize_selections(node.view) if node.view else None
			if selections_summary:
				result += '  ' * (indent + 1)
				result += selections_summary
				result += '\n'
			for child in node.children:
				result += show_node(child, indent + 1)
			return result
		result = ''
		for child in cls.root_node.children:
			result += show_node(child, 0)
		return result
	@classmethod
	def on_close(cls, view):
		if str(view.id()) in cls.node_index:
			cls.node_index[str(view.id())].is_open = False
	@classmethod
	def on_modified(cls, view):
		if str(view.id()) in cls.node_index:
			cls.node_index[str(view.id())].was_modified = True
	def run(self):
		view = self.window.new_file()
		view.set_name('Your FlowTree')
		view.set_scratch(True)
		edit = view.begin_edit('DisplayFlowTree')
		try:
			view.insert(edit, 0, FlowTreeCommand.flow_tree())
		finally:
			view.end_edit(edit)

class FlowTreeListener(sublime_plugin.EventListener):
	def on_activated(self, view):
		FlowTreeCommand.on_activated(view)
	def on_deactivated(self, view):
		FlowTreeCommand.on_deactivated(view)
	def on_post_save(self, view):
		FlowTreeCommand.on_post_save(view)
	def on_close(self, view):
		FlowTreeCommand.on_close(view)
	def on_modified(self, view):
		FlowTreeCommand.on_modified(view)