

###### general register file
registers = {
    'r0': 0,
    'r1': 11,
    'r2': 22,
    'r3': 33,
    'r4': 44,
    'r5': 55,
    'r6': 66,
    'r7': 77,
    'sp': 0,
    'fp': 0,
    'lr': None,
    'pc': None,
}


####### Program flow is a class
class Flow:
    def __init__(self, obj, cur_label="start"):
        self.cur_label = cur_label
        self.context = obj[cur_label]
        self.lineno = 0

    def get_inst(self):
        return self.context[self.lineno]

    def step(self):  #pc++
        self.lineno += 1

    def __str__(self):
        return "@%s+%d" % (self.cur_label, self.lineno)


stack = []
proc_state_word = {}
isa = isinstance


def display_gp_regs():
    gp_regs = ('r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r7')
    regs = registers.items()
    regs.sort()
    for key, value in regs:
        if key in gp_regs:
            print "|     %s" % key,
    
    print "\n", 
    
    for key, value in regs:
        if key in gp_regs:
            print "|%7d" % value,


def display_pc():
    print registers['pc'], "->" ,
    print to_string(registers['pc'].get_inst())
        

def display_context():
    for inst in registers['pc'].context:
        print to_string(inst)

def display_remaining_context():
    for i in range(registers['pc'].lineno, len(registers['pc'].context)):    
        print to_string(registers['pc'].context[i])   


def display_stack():
    global fp
    if len(stack) > 0:
        for i in range(len(stack)):
            if registers['fp'] == i:
                star = "*"
            else:
                star = ""
            print "| %d %s" % (stack[i], star), 
    print "| top"

import sys

def display_ir():
    x = registers['pc'].current()
    print to_string()

def execute(exe):
    """
    In this implementation of virtual machine, PC(programmer counter) is 
    a iterator object whose next() method always give the instuction to execute
    """

    x = registers['pc'].get_inst()  # x is just like the instruction_register
    registers['pc'].step()          # pc ++


    if x[0] == "not":
        try:
            (_, dest, src) = x
        except ValueError:
            raise OperandError("%s should have 2 operand" % x[0])

        if not dest in registers:
            raise RegisterError("%s is not a valid dest" % dest)

        if not src in registers:
            raise RegisterError("%s is not a valid src" % src)

        if isa(src, int):
            registers[dest] = ~src
        else:
            registers[dest] = ~registers[src]

    elif x[0] in ("add", "sub", "and", "or"):     # arithmetic
        try:
            (op, dest, src1, src2) = x
        except ValueError:
            raise OperandError("%s should have 3 operands" % x[0])

        if not dest in registers:
            raise RegisterError("%s is not a valid dest" % dest)

        if not src1 in registers:
            raise RegisterError("%s is not a valid src" % src1)

        if isa(src2, int):        #src2 is immediate
            if op == "add":
                registers[dest] = registers[src1] + src2
            elif op == "sub":
                registers[dest] = registers[src1] - src2
            elif op == "and":
                registers[dest] = registers[src1] & src2
            elif op == "or":
                registers[dest] = registers[src1] | src2
        else: # src2 is from register
            if not src1 in registers:
                raise RegisterError("%s is unknown" % src2)
            if op == "add":
                registers[dest] = registers[src1] + registers[src2]
            elif op == "sub":
                registers[dest] = registers[src1] - registers[src2]
            elif op == "and":
                registers[dest] = registers[src1] & registers[src2]
            elif op == "or":
                registers[dest] = registers[src1] | registers[src2]

    elif x[0] in ("push", "pop"):
        try:
            (op, reg) = x
        except ValueError:    
            raise OperandError("%s should have 1 operand" % x[0])

        if not reg in registers:   
            raise RegisterError("%s is not a valid register" % reg)

        if op == "push":
            stack.append(registers[reg])
            registers['sp'] += 1
        
        elif op == "pop":
            registers[reg] = stack.pop()
            registers['sp'] -=  1

    elif x[0] == "call":

        registers['lr'] = registers['pc']  # store next "pc" in link register

        (_, target) = x

        if target in exe:
            registers['pc'] = Flow(exe, target)    # Transfer to a new flow   
        else:
            raise RuntimeError("Cannot find the calling target")

    elif x[0] == "ret":
        registers['pc'] = registers['lr'] # get the return address from "ret"

    elif x[0] == "halt":
        print "The computer is halted."
        sys.exit()




############## exception
class StackException(Exception):
    code = 1
    def __init__(self, message):
        self.message = message

    # print e
    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return '{0}'.format(self.message)


class RegisterError(StackException):
    pass

class OperandError(StackException):
    pass

class StackError(StackException):
    pass

class SyntaxError(StackException):
    pass

class RuntimeError(StackException):
    pass


################ Parse
def parse_line(s):
    "Read a expression from a string."
    return read_from(tokenize(s))

 
def tokenize(s):
    "Convert a string into a list of tokens."
    return s.replace(',', ' ').split()

def read_from(tokens):
    "read a instruction list from a sequence of tokens."
    inst = []
    for t in tokens:
        inst.append(atom(t))
    return inst
 
def atom(token):
    "Token can be a symbol or a immediate integer, e.g. r1 or 55"
    try: 
        return int(token)
    except ValueError:
        return str(token)

def to_string(l):
    "Convert the list back to the string"
    if len(l) == 0:
        raise(SyntaxError("instruction is unknown"))
    s = ""
    s += l[0]
    if len(l) > 1:
        s += " "
        s += l[1]
        if len(l) > 2:
            for t in l[2:]: 
                s += ", "
                s += str(t)
    return s


################# assemble
def assemble(src_code):
    "assemble the source code to code blocks associated with labels"
    lines = src_code.split("\n")
    current_label_name = "unknown"

    symtab = {}

    import re
    label_pattern = re.compile("[A-Za-z][A-Za-z0-9]*:") 

    for l in lines:
        
        if label_pattern.match(l):   #match the label
            label_name = label_pattern.search(l).group()[:-1]
            symtab[label_name] = [] # create an entry in the global_labels
            current_label_name = label_name
            continue  # label line has no instruction
        inst_list = parse_line(l)
        if len(inst_list) > 0:   # skip the blank one
            symtab[current_label_name].append(inst_list)


    print symtab
    return symtab



################## keep running
def run(obj):
    registers['pc'] = Flow(obj)
    while True:
        display_pc()
        #display_context()
        execute(obj)
        display_stack()
        display_gp_regs()
        print "\n"


