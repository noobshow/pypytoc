from pypy.rpython import lltype


_nodename_count = {}

class LLVMNode(object):
    __slots__ = "".split()

    def reset_nodename_count():
        global _nodename_count
        _nodename_count = {}
    reset_nodename_count = staticmethod(reset_nodename_count)

    def make_name(self, name):
        " helper for creating names"
        if " " in name or "<" in name: 
            name = '"%s"' % name

        global _nodename_count 
        if name in _nodename_count:
            postfix = '_%d' % _nodename_count[name]
            _nodename_count[name] += 1
        else:
            postfix = ''
            _nodename_count[name] = 1
        return name + postfix

    def make_ref(self, prefix, name):
        return self.make_name(prefix + name)

    def setup(self):
        pass

    # __________________ before "implementation" ____________________
    #def writedatatypedecl(self, codewriter):
    #    """ write out declare names of data types 
    #        (structs/arrays/function pointers)
    #    """

    def writeglobalconstants(self, codewriter):
        """ write out global values.  """

    def writedecl(self, codewriter):
        """ write function forward declarations. """ 

    def writecomments(self, codewriter):
        """ write operations strings for debugging purposes. """ 

    # __________________ after "implementation" ____________________
    def writeimpl(self, codewriter):
        """ write function implementations. """ 

class ConstantLLVMNode(LLVMNode):
    __slots__ = "".split()

    def get_ref(self):
        """ Returns a reference as used for operations in blocks. """        
        return self.ref

    def get_pbcref(self, toptr):
        """ Returns a reference as a pointer used per pbc. """        
        return self.ref

    def constantvalue(self):
        """ Returns the constant representation for this node. """
        raise AttributeError("Must be implemented in subclass")

    # ______________________________________________________________________
    # entry points from genllvm

    def writeglobalconstants(self, codewriter):
        p, c = lltype.parentlink(self.value)
        if p is None:
            codewriter.globalinstance(self.ref, self.constantvalue())
