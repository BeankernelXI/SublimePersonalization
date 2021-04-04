class Flags:
  # Usage:
  # FLAG_FOO, FLAG_BAR, FLAG_BAZ, *_ = Flag()
  def __init__(self, max_count=32):
    self.flag = 1
    self.limit = 1<<(max_count-1)
  def __iter__(self):
    return self
  def __next__(self):
    if self.flag >= self.limit:
      raise StopIteration
    old_flag = self.flag
    self.flag <<= 1
    return old_flag
  next = __next__  # python2.x compatibility.
