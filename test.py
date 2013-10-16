from stack import run, assemble

code = '''
sum:
    push r2
    ret


start:
    and r0, r0, 0
    add r1, r0, 14
    add r2, r0, 5
    sub r3, r0, 10
    push r1
    push r2
    push r3

    call sum

    
    halt
'''
9152498253


run(assemble(code))