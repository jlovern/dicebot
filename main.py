import re
import operator as op
from random import randint
import math
import discord

import configparser

config = configparser.ConfigParser()
config.read("config.ini")

def fn_if(cond,true,false):
    if cond:
        return true
    return false

ops_dict = {"*": (2,op.mul),
            "@": (2,lambda a,b: sum([randint(1,int(a)) for i in range(int(b))])),
            "-": (2,op.sub),
            "+": (2,op.add),
            "/": (2,op.truediv),
            "%": (2,op.mod),
            "^": (2,op.pow),
            "=": (2,op.eq),
            "abs": (1,op.abs),
            "<": (2,op.gt),
            ">": (2,op.lt),
            "min": (2,min),
            "max": (2,max),
            "fnif":(3,fn_if),
            "sqrt":(1,math.sqrt)}
ops_precedence = {"@":4,"^":3,"*":2,"/":2,"%":2,"+":1,"-":1,"<":0,"=":0,">":0}
isDigit      = lambda  d: bool(re.search(r"(\d|\.)",d))
isLetter     = lambda  l: bool(re.search(r"[a-z]",l))
isOperator   = lambda  o: bool(re.search(r"[\+\-\*/%!^@<>=]",o))
isComma      = lambda  c: c==","
isLeftParen  = lambda lp: lp=="("
isRightParen = lambda rp: rp==")"
class Token:
    def __init__(self,token_type,token_value):
        self.type = token_type
        self.value = token_value
    def __str__(self):
        return self.type+" "+self.value
    def __repr__(self):
        return f'"{self.value}"'

def tokenizer(pattern):
    pattern = re.sub("\s","",pattern)
    result = []
    numBuffer = ""
    opBuffer = ""
    parenStack = 0
    last = ""
    decFlag = False
    parenFlag = False
    for i,c in enumerate(pattern):
        if isDigit(c):
            if last == "Letter" or (decFlag==True and c=="."):
                raise SyntaxError(f"Invalid code at: {pattern[max(0,i-3):min(i+3,len(pattern))]}")
            elif last=="RP":
                result.append(Token("Op","*"))
            numBuffer += c
            last = "Digit"
        elif numBuffer != "":
            result.append(Token("Literal",numBuffer))
            numBuffer = ""
            decFlag = False
        if isOperator(c):
            if last in ["Op","Comma","LP"]:
                if c=="-":
                    numBuffer += c
                else:
                    raise SyntaxError(f"Invalid code at: {pattern[max(0,i-3):min(i+3,len(pattern))]}")
            elif last == "Letter":
                raise SyntaxError(f"Invalid code at: {pattern[max(0,i-3):min(i+3,len(pattern))]}")
            else: #last is a RP or a Digit
                result.append(Token("Op",c))
            last = "Op"
        if isLetter(c):
            opBuffer += c
            if last in ["Digit","RP"]:
                result.append(Token("Op","*"))
            last = "Letter"
        if isComma(c):
            if last in ["Digit","RP"]:
                result.append(Token("Comma",","))
            else:
                raise SyntaxError(f"Invalid code at: {pattern[max(0,i-3):min(i+3,len(pattern))]}")
            last = "Comma"
        if isLeftParen(c):
            if last in ["Digit","RP"]:
                result.append(Token("Op","*"))
            if last=="Letter":
                result.append(Token("Function",opBuffer))
                parenFlag = True
                opBuffer = ""
                result.append(Token("LPF","("))
            else:
                result.append(Token("LP","("))
            parenStack += 1
            last = "LP"
        if isRightParen(c):
            if parenStack==0:
                raise SyntaxError(f"Mismatched Parens at: {pattern[max(0,i-3):min(i+3,len(pattern))]}")
            if last in ["Letter","Comma","Op"]:
                raise SyntaxError(f"Invalid code at: {pattern[max(0,i-3):min(i+3,len(pattern))]}")
            if last=="LP" and not parenFlag:
                result.pop()
            else:
                result.append(Token("RP",")"))
            parenStack -= 1
            parenFlag = False
            last = "RP"
    if numBuffer != "":
        result.append(Token("Literal",numBuffer))
    if opBuffer != "":
        raise SyntaxError("OpBuffer not empty!")
    return result

def RPNify(parseTree):
    def evaluatePrecedence(item1,item2):
        return ops_precedence[item1.value]<ops_precedence[item2.value]
    stack = [Token("Empty","")]
    out = []
    for i,item in enumerate(parseTree):
        print(f"-------\nparseTree:{parseTree[i:]}\nItem: {item}\nStack: {stack}\nout:{out}\n")
        if item.type=="Literal":
            out.append(item)
        elif item.type=="Op":
            if stack[-1].type != "Op" or evaluatePrecedence(stack[-1],item):
                stack.append(item)
            else:
                while stack[-1].type == "Op" and not evaluatePrecedence(stack[-1],item):
                    #print(f"A)Popping {stack[-1]}\n")
                    out.append(stack.pop())
                stack.append(item)
        elif item.type in ["LP","Function","LPF"]:
            stack.append(item)
        elif item.type=="Comma":
            while stack[-1].type !="LPF":
                #print(f"B)Popping {stack[-1]}\n")
                out.append(stack.pop())
        elif item.type == "RP":
            while stack[-1].type not in ["LP","LPF"]:
                out.append(stack.pop())
            if stack[-1].type == "LPF":
                stack.pop()
                #print(f"C)Popping {stack[-1]}\n")
                out.append(stack.pop())
            else:
                stack.pop()
    while stack[-1].type != "Empty":
        out.append(stack.pop())
    return out

def eval_RPN(rpn_arry):
    stack = []
    for item in rpn_arry:
        if item.type =="Literal":
            stack.append(float(item.value))
        else:
            temp = [stack.pop() for i in range(ops_dict[item.value][0])]
            stack.append(ops_dict[item.value][1](*temp))
    return stack[0]

doit = lambda d: eval_RPN(RPNify(tokenizer(d)))

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content == "!dicebot test":
        await message.channel.send("I'm here!")
    elif message.content.startswith('!dicebot '):
        await message.channel.send(doit(message.content[9:]))
    

client.run(config['DISCORD']['Bot_Token'])