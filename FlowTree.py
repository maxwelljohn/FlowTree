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
    def completed(self):
        return not self.is_open and all([child.completed() for child in self.children])
    def clear_completed_children(self):
        self.children = [child for child in self.children if not child.completed()]

class WriteTreeCommand(sublime_plugin.TextCommand):
    def run(self, edit, tree):
        self.view.replace(edit, sublime.Region(0, self.view.size()), tree)

class FlowTreeCommand(sublime_plugin.WindowCommand):
    root_node = FlowNode(None, [], False, True, None)
    node_hist = [root_node]
    node_index = {}
    searches_in_view = defaultdict(list)
    flowtree_views = []
    @classmethod
    def summarize_selections(cls, view):
        sels = view.sel()
        if len(sels) > 1:
            return "Multiple blocks of text left selected"
        elif len(sels) == 0:
            return None
        else:
            sel = view.substr(sels[0])
            if sel == '':
                return None
            elif len(sel) > 50:
                return "Over 50 characters of text left selected"
            else:
                return "Text left selected: " + repr(sel)
    @classmethod
    def visit_node(cls, view, is_search=False):
        vid = str(view.id())
        if is_search:
            last_search = view.find_all('Searching \d+ files for .*$')[-1]
            desc = view.substr(last_search)
            node_id = vid + '-' + desc
        else:
            desc = os.path.basename(view.file_name())
            node_id = vid

        if node_id in cls.node_index:
            cls.node_hist.append(cls.node_index[node_id])
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
            # Also, searches typically don't inspire other searches.
            hist = [node for node in cls.node_hist if not node.is_search] if is_search else cls.node_hist
            hist[-1].children.append(new_node)
            cls.node_index[node_id] = new_node
            if is_search:
                for prev_search in cls.searches_in_view[vid]:
                    prev_search.is_open = False
                cls.searches_in_view[vid].append(new_node)
            cls.node_hist.append(new_node)

        # Prevent history from getting too big.
        if len(cls.node_hist) > 10000:
            cls.node_hist = cls.node_hist[-5000:]
    @classmethod
    def on_activated(cls, view):
        if view.file_name():
            cls.visit_node(view)
            cls.update_flowtree_views()
    @classmethod
    def on_post_save(cls, view):
        # This if should always be True but maybe there's something I don't know.
        if view.file_name():
            cls.visit_node(view)
            cls.update_flowtree_views()
    @classmethod
    def on_deactivated(cls, view):
        if 'Find Results' in view.name():
            cls.visit_node(view, True)
            cls.update_flowtree_views()
    @classmethod
    def flow_tree(cls):
        def show_node(node, indent):
            result = '  ' * indent
            # Checked box for closed files; unchecked box for open files.
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
        cls.root_node.clear_completed_children()
        for child in cls.root_node.children:
            result += show_node(child, 0)
        return result
    @classmethod
    def on_close(cls, view):
        vid = str(view.id())
        if vid in cls.node_index:
            cls.node_index[vid].is_open = False
            cls.update_flowtree_views()
        elif vid in cls.searches_in_view:
            for node in cls.searches_in_view[vid]:
                node.is_open = False
            cls.update_flowtree_views()
    @classmethod
    def on_modified(cls, view):
        vid = str(view.id())
        if vid in cls.node_index:
            cls.node_index[vid].was_modified = True
            cls.update_flowtree_views()
    @classmethod
    def update_flowtree_views(cls):
        for view in cls.flowtree_views:
            view.run_command('write_tree', {'tree': cls.flow_tree()})
    def run(self):
        my_cls = FlowTreeCommand
        view = self.window.new_file()
        view.set_name('Your FlowTree')
        view.set_scratch(True)
        my_cls.flowtree_views.append(view)
        my_cls.update_flowtree_views()

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