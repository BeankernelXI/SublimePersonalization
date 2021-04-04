import sublime
import sublime_plugin


class GlobalKeyInit(sublime_plugin.TextCommand):

  def __init__(self, view):
    self.view = view # grr this took too long to find
    if not hasattr(self.view, 'key'):     self.view.key = 0
    if not hasattr(self.view, 'max_key'): self.view.max_key = 0

class SelectionGroupsHelperCommand(sublime_plugin.TextCommand):

# leaving this here since it is poorly documented
  # def __init__(self, view):
  #   self.view = view

  def rotate_group(self):
    print("rotate_group")
    if not self.current_group():
      if len(self.view.sel() ) == 1: return
      self.merge_group()
    regions = self.current_group()
    current_region = self.view.sel()[-1]
    next_region = regions[0]
    for region in regions:
      if region != current_region and region.end() >= current_region.end():
        next_region = region
        break
    self.view.sel().clear()
    self.view.sel().add(next_region)
    self.view.show(next_region.b)

  def merge_group(self):
    print("merge_group")
    self.add_group_if_needed()
    self.view.add_regions( self.key_str(), list(self.view.sel() ) + self.current_group(),
                          'source', 'dot', sublime.DRAW_NO_FILL )

  def recall_group(self):
    print("recall_group")
    backup = self.view.sel()[0]
    self.view.sel().clear()
    if not self.current_group(): self.view.show(backup)
    self.view.sel().add_all(self.current_group() or [backup] )

  def next_group(self):
    print("next_group")
    if not self.view.max_key: return

    this_group = self.current_group()
    self.view.erase_regions(self.key_str() )
    self.view.add_regions( self.key_str() , this_group,
                          'source', 'dot', sublime.HIDDEN )
    self.next_key()

    next_group = self.view.get_regions(self.key_str() )
    self.view.erase_regions(self.key_str() )
    self.view.add_regions( self.key_str() , next_group,
                          'source', 'dot', sublime.DRAW_NO_FILL )

  def clear_group(self):
    print("clear_group")
    if self.view.key == self.min_key():
      self.clear_all()
      return
    if self.view.key is not self.view.max_key:
      self.shift_over_key()
    # kinda lazy to do it this way. oh well.
    self.view.erase_regions(self.max_key_str() )

    self.view.key = self.min_key()
    self.view.max_key -= 1

  def shift_over_key(self):
    # relying on key <= max_key seems reasonable
    for key in range(self.view.key,self.view.max_key): # REMEMBER: [range)
      next_group = self.view.get_regions(str(key+1) )
      self.view.erase_regions(self.key_str() )
      self.view.add_regions( str(key) , next_group,
                            'source', 'dot', sublime.HIDDEN )

  def clear_all(self):
    for key in range(self.min_key(),self.view.max_key + 1): # REMEMBER: [range)
      self.view.erase_regions(str(key)) # this is bad style, but for now I can't be bothered
    self.view.max_key = self.min_key()

  def current_group(self):
    return self.view.get_regions(self.key_str() )

  def add_group_if_needed(self):
    if self.view.key == self.min_key():
      self.view.max_key += 1
      self.view.key = self.view.max_key

  def next_key(self):
    if self.view.max_key is self.min_key(): return self.min_key()
    key, max_key = self.view.key, self.view.max_key
    self.view.key = (key+1) % (max_key +1 - self.min_key())

  def min_key(self):
    # this should probably be a constant but it doesn't bother me yet
    return 0

  def update_status(self):
    NO_EMOJI = ''
    EMPTY_EMOJI = '🥪'
    GROUP_EMOJI = '🥑'

    key = self.view.key
    max_key = self.view.max_key
    emoji = NO_EMOJI if max_key==0 else EMPTY_EMOJI if key==0 else GROUP_EMOJI
    self.view.set_status('group_status', emoji)

  def key_str(self):
    return str(self.view.key)
  def max_key_str(self):
    return str(self.view.max_key)

# ----- Core Commands ----------------------------------------

class RotateGroupCommand(SelectionGroupsHelperCommand):
  def run(self, edit):
    print("RotateGroup")
    self.rotate_group()
    self.update_status()

class MergeGroupCommand(SelectionGroupsHelperCommand):
  def run(self, edit):
    print("MergeGroup")
    self.merge_group()
    self.update_status()

class RecallGroupCommand(SelectionGroupsHelperCommand):
  def run(self, edit):
    print("RecallGroup")
    self.recall_group()
    self.update_status()

class NextGroupCommand(SelectionGroupsHelperCommand):
  def run(self, edit):
    print("NextGroup")
    self.next_group()
    self.update_status()

class ClearGroupCommand(SelectionGroupsHelperCommand):
  def run(self, edit):
    print("ClearGroup")
    self.clear_group()
    self.update_status()

class TestGroupCommand(SelectionGroupsHelperCommand):
  def run(self, edit):
    v = self.view
    print(v.key)
