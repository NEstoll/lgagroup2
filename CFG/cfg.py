from dataclasses import dataclass
import sys
import copy
from typing import List
 #Usage: python cfg.py <input_file_name>
input_file_name = sys.argv[1]

file = open(input_file_name)
lines = file.readlines()
cfg = []

#Set up cfg array
for line in lines:
    cfg.append(line.split())
file.close()

terminals = []
non_terminals = []

#Forces cfg array to conform to the form [Non-terminal, terminal, terminal....] for each line. The "->" is implicit between
#the first and second elements of each line.
#A list of terminals and a list of non-terminals are also created
i = 0
while i < len(cfg):
    j = 0
    while j < len(cfg[i]):
        # print(i,j)
        if cfg[i][j] == "->":
            # print("POP")
            cfg[i].pop(j)
            j -= 1
            # print(j)
        elif j == 0 and cfg[i][j] == "|":
            cfg[i][j] = cfg[i-1][0]
        elif cfg[i][j] == "|":
            tmp = []
            tmp.append(cfg[i][0])
            tmp = tmp + cfg[i][j+1:]
            cfg.insert(i+1, tmp)
            while j < len(cfg[i]):
                cfg[i].pop(j)
        elif j == 0:
            if not cfg[i][j] in non_terminals:
                non_terminals.append(cfg[i][j])
        elif cfg[i][j].islower():
            if not cfg[i][j] in terminals:
                if cfg[i][j] != "lambda":
                    terminals.append(cfg[i][j])
        j+=1
    i += 1

#printing the output.

print("Grammar Non-Terminals:")
s = ""
for t in non_terminals:
    s += t + " "
print(s)

print("Grammar Terminals:")
d = ""
for t in terminals:
    d += t + " "
print(d)

print("Grammar Symbols: ")
print(s, d)

print("Grammar Rules")

for c in cfg:
    s = ""
    for i in range(len(c)):
        s += c[i] + " "
        if(i == 0):
            s += "-> "
    print(s)
# print(cfg)
non_terminal = str

# given P the production rules (default arg for now)
# would also need to be given terminals, nonterminals (could be cfg object)
# but im lazy
# and stack T is empty on first call.

def derives_to_lambda(L: non_terminal, T: List[str], P=cfg):
    # returns true if exists production rule permitting L *=> lambda
    # print(f"trace, {L=}, {T=}")
    for prod in P:
        if prod[0] != L: continue
        if prod in T: continue
        if "lambda" in prod: return True
        rhs = prod[1:]
        if any(item in terminals for item in rhs): continue
        all_derive_lambda = True
        for non_term in rhs:
            if non_term in terminals: continue
            if '$' in non_term: continue
            T.append(prod)
            all_derive_lambda = derives_to_lambda(non_term, copy.deepcopy(T))
            # print(f"trace, {non_term=}, {all_derive_lambda=}")
            T.pop()
            if not all_derive_lambda: break
        if all_derive_lambda:
            return True
    return False

print(f"{derives_to_lambda('startGoal', [])=}")

# seq is a valid seq of grammar elements, list
# T is an empty set on first call of procedure
# again, adding cfg list
sequence = List[str]
def first_set(seq: sequence, T, P=cfg):
    # returns set of terminals {t in alphabet | seq => tpi},
    # updated set 
    # print(f"first trace, {seq=}, {T=}")
    head, tail = seq[0], seq[1:]
    
    if head in terminals:
        s = set()
        s.add(head)
        return s, T

    # F for first set
    F = set()
    if head not in T:
        T.add(head)
        for prod in P:
            if prod[0] != head: continue
            R = prod[1:]
            if "lambda" in R:
                continue
            # I for ignorable
            G, I = first_set(R, T)
            F = F.union(G)
    if derives_to_lambda(head, []) and len(tail) > 0:
        G, I = first_set(tail, T)
        F = F.union(G)
    return F,T

print(f"{first_set(['A', '$'], set())=}")

def follow_set(A: non_terminal, T: set, P=cfg):
    if A in T:
        return set(), T
    T.add(A)
    # F for follow set
    F = set()
    for p in P:
        LHS, RHS = p[0], p[1:]
        if A not in RHS:
            continue
        # If it's the last element in the prod rule
        for index, gamma in enumerate(RHS):
            if gamma == A:
                pi = RHS[index + 1:]
                if len(pi) > 0:
                    # I for ignorable
                    G, I = first_set(pi, set())
                    F = F.union(G)
                term_and_end = set(terminals)
                term_and_end.add("$")
                empty = len(pi) == 0
                pi_in_empty = len(set(pi).intersection(term_and_end)) == 0
                dtl = True 
                for sym in pi:
                    if sym in non_terminals:
                        if not derives_to_lambda(sym, [], P):
                            dtl = False
                if empty or (pi_in_empty and dtl):
                    G, I = follow_set(LHS, T)
                    F = F.union(G)
    return F, T
                    
print(f"{follow_set('Var', set())=}") 
   
def predict_set(seq: sequence, P=cfg):
    ps=first_set(sequence,set())
    if derives_to_lambda(sequence[0],list()):
        ps.union(follow_set(sequence))
    return ps

def ll1_table(P=cfg):
    #returns a map of maps
    #note that the rule indexes in the LL table start at 0 and not
    #1 as seen in the lecture slides. This was done to make future list
    #access easier
    cntr=0
    T=map()
    for prod in P:
        #ps for predict set
        ps=predict_set(prod)
        T[prod[0]]=map()
        for term in ps:
                T[prod[0]][term]=cntr
        cntr+=1
    return T

#List<List<GrammarElements>> Pcontaining production rules, indexed numerically 
#Map<NonTerminal, Map<Terminal, int>> LL1 table for P
#Queue tokens conataining the input tokens
def parse_tree(P, LL1, tokens):
    # Implement the logic for building a parse tree from a set of productions P, an LL(1) parsing table, and of course a
    #token stream. Arrange your token stream to simply be an object that reads lines from a file that contain either a
    #TOKENTYPE or a TOKENTYPE srcValue per line. You will hand craft these input files for now — eventually they
    #will be generated by a proper lexer. Don’t make the parse tree too complicated, trees are just lists of lists ;).

    root = Node()
    current = root
    stack = list()
    stack.append("S") #starting symbol
    while (stack.count != 0) :
        top = stack.pop()
        if top == "*": #end of rule character
            current = current.parent
        elif top.islower() and top == tokens.peek() :
            current.children.append(tokens.pop())
        elif top.isupper() :
            new = Node()
            stack.append("*")
            for rule in reversed(P[LL1[top][tokens.peek()]]):
                stack.append()
            new.data = top
            new.parent = current
            current.children.append(new)
            current = new



            
    

#tree class
class Node:
    def __init__(self):
        self.children = []
        self.data = None
        self.parent = None
