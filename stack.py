





####### 
class Code(dict):
    """
    In Stack's eye, code(program), whether executable or readable, is a hash table
        key: labels in the program
        value: a list of instructions under the label
    """
    pass


####### Program flow is a object instead of a number
class Flow(object):
    "Create a execution flow from a obj file. The default start point is 'start'"
    def __init__(self, exe, cur_label="start"):
        self.cur_label = cur_label
        self.context = exe[cur_label]
        self.lineno = 0

    def get_inst(self):
        return self.context[self.lineno]

    def forward(self):  #pc++
        self.lineno += 1

    def __str__(self):
        return "@%s+%d" % (self.cur_label, self.lineno)


class Registers(dict):
    "Register is just a dict"
    def __init__(self, parms=(), args=()):
        self.update(zip(parms,args))
        
    def __str__(self):
        regs = self.items()
        regs.sort()
        return ", ".join([": ".join([name, str(val)]) for name, val in regs])
         


class Stack(list):
    def push(self, val):
        self.append(val)

    def pop(self):
        return self.pop()




isa = isinstance


class Machine(object):

    def __init__(self):
        self.stack = Stack()
        self.registers = Registers()
        # register the regs here
        self.registers.update({
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
        })
        self.halt = False
        self.text_segment = {}

    def load(self, exefile):
        """
        Here, the loading machanism is very simple. No mapping is required
        """
        self.exe = exefile

        # get the pc ready
        self.registers['pc'] = Flow(exefile)


    def run(self):
        "Run forever until halt"
        while True:
            print self.registers['pc']
            print to_string(self.registers['pc'].get_inst())
            print self.registers
            print self.stack
            self.step()
            if self.halt == True: break
        print "The computer halts quietly~~~"


    def step(self):
        """
        In this implementation of virtual machine, PC(programmer counter) is 
        a iterator object whose next() method always give the instuction to execute
        """

        x = self.registers['pc'].get_inst()  # x is just like the instruction_register
        self.registers['pc'].forward()      # pc++

        if x[0] == "not":
            try:
                (_, dest, src) = x
            except ValueError:
                raise OperandError("%s should have 2 operand" % x[0])

            if not dest in self.registers:
                raise RegisterError("%s is not a valid dest" % dest)

            if not src in self.registers:
                raise RegisterError("%s is not a valid src" % src)

            if isa(src, int):
                self.registers[dest] = ~src
            else:
                self.registers[dest] = ~self.registers[src]

        elif x[0] in ("add", "sub", "and", "or"):     # arithmetic
            try:
                (op, dest, src1, src2) = x
            except ValueError:
                raise OperandError("%s should have 3 operands" % x[0])

            if not dest in self.registers:
                raise RegisterError("%s is not a valid dest" % dest)

            if not src1 in self.registers:
                raise RegisterError("%s is not a valid src" % src1)

            if isa(src2, int):        #src2 is immediate
                if op == "add":
                    self.registers[dest] = self.registers[src1] + src2
                elif op == "sub":
                    self.registers[dest] = self.registers[src1] - src2
                elif op == "and":
                    self.registers[dest] = self.registers[src1] & src2
                elif op == "or":
                    self.registers[dest] = registers[src1] | src2
            else: # src2 is from register
                if not src1 in registers:
                    raise RegisterError("%s is unknown" % src2)
                if op == "add":
                    self.registers[dest] = self.registers[src1] + self.registers[src2]
                elif op == "sub":
                    self.registers[dest] = self.registers[src1] - self.registers[src2]
                elif op == "and":
                    self.registers[dest] = self.registers[src1] & self.registers[src2]
                elif op == "or":
                    self.registers[dest] = self.registers[src1] | self.registers[src2]

        elif x[0] in ("push", "pop"):
            try:
                (op, reg) = x
            except ValueError:    
                raise OperandError("%s should have 1 operand" % x[0])

            if not reg in self.registers:   
                raise RegisterError("%s is not a valid register" % reg)

            if op == "push":
                self.stack.push(self.registers[reg])
                self.registers['sp'] += 1
            
            elif op == "pop":
                self.registers[reg] = self.stack.pop()
                self.registers['sp'] -=  1

        elif x[0] == "call":

            self.registers['lr'] = self.registers['pc']  # store next "pc" in link register

            (_, target) = x

            if target in self.exe:
                self.registers['pc'] = Flow(self.exe, target)    # Transfer to a new flow   
            else:
                raise RuntimeError("Cannot find the calling target: %s" % target) 



        elif x[0] == "ret":
            self.registers['pc'] = self.registers['lr'] # get the return address from "ret"

        elif x[0] == "halt":
            self.halt = True




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



def load(obj):
    global registers
    registers['pc'] = Flow(obj)


