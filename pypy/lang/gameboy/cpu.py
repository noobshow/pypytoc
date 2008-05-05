from pypy.lang.gameboy import constants


class Register(object):
    def __init__(self, cpu, value=0):
        self.resetValue = self.value = value
        self.cpu = cpu
        if value != 0:
            self.set(value)
        
    def reset(self):
        self.value = self.resetValue
        
    def set(self, value, useCycles=True):
        self.value = value & 0xFF
        if useCycles:
            self.cpu.cycles -= 1
        
    def get(self, useCycles=True):
        return self.value
    
    def add(self, value, useCycles=True):
        self.set(self.get(useCycles)+value, useCycles)
        
    def sub(self, value, useCycles=True):
        self.set(self.get(useCycles)-value, useCycles)
    
# ------------------------------------------------------------------------------

class DoubleRegister(Register):
    
    def __init__(self, cpu, hi=None, lo=None, resetValue=0):
        self.cpu = cpu
        if isinstance(hi, (Register)) :
            self.hi = hi
        else:
            self.hi = Register(self.cpu)
        if lo==None:
            self.lo = Register(self.cpu)
        else:
            self.lo = lo
        self.resetValue = resetValue
        
    def set(self, hi=0, lo=None, useCycles=True):
        if (lo is None):
            self.setHi(hi >> 8, useCycles)
            self.setLo(hi & 0xFF, useCycles)
            if useCycles:
                self.cpu.cycles += 1
        else:
            self.setHi(hi, useCycles)
            self.setLo(lo, useCycles) 
    
    def reset(self):
        self.set(self.resetValue, None, useCycles=False)
            
    def setHi(self, hi=0, useCycles=True):
        self.hi.set(hi, useCycles)
    
    def setLo(self, lo=0, useCycles=True):
        self.lo.set(lo, useCycles)
        
    def get(self, useCycles=True):
        return (self.hi.get(useCycles)<<8) + self.lo.get(useCycles)
    
    def getHi(self, useCycles=True):
        return self.hi.get(useCycles)
        
    def getLo(self, useCycles=True):
        return self.lo.get(useCycles)
    
    def inc(self, useCycles=True):
        self.set(self.get(useCycles) +1, None, useCycles)
        if useCycles:
            self.cpu.cycles -= 1
        
    def dec(self, useCycles=True):
        self.set(self.get(useCycles) - 1, None, useCycles)
        if useCycles:
            self.cpu.cycles -= 1
        
    def add(self, n=2, useCycles=True):
        self.set(self.get(useCycles) + n, None, useCycles)
        if useCycles:
            self.cpu.cycles -= 2
    
# ------------------------------------------------------------------------------

class ImmediatePseudoRegister(object):
        def __init__(self, cpu, hl):
            self.cpu = cpu
            self.hl = hl
            
        def set(self, value, useCycles=True):
            self.cpu.write(self.hl.get(useCycles), value) # 2 + 0
            if not useCycles:
                self.cpu.cycles += 2
        
        def get(self, useCycles=True):
            if not useCycles:
                self.cpu.cycles += 1
            return self.cpu.read(self.hl.get(useCycles)) # 1
    
# ------------------------------------------------------------------------------
  
class FlagRegister(Register):
    
    def __init__(self, cpu):
        self.cpu = cpu
        self.reset()
         
    def reset(self, keepZ=False, keepN=False, keepH=False, keepC=False,\
                keepP=False, keepS=False):
        if not keepZ:
            self.zFlag = False
        if not keepN:
            self.nFlag = False
        if not keepH:
            self.hFlag = False
        if not keepC:
            self.cFlag = False
        if not keepP:
            self.pFlag = False
        if not keepS:
            self.sFlag = False
        self.lower = 0x00
            
    def get(self, useCycles=True):
        value = 0
        value += (int(self.cFlag) << 4)
        value += (int(self.hFlag) << 5)
        value += (int(self.nFlag) << 6)
        value += (int(self.zFlag) << 7)
        return value + self.lower
            
    def set(self, value, useCycles=True):
        self.cFlag = bool(value & (1 << 4))
        self.hFlag = bool(value & (1 << 5))
        self.nFlag = bool(value & (1 << 6))
        self.zFlag = bool(value & (1 << 7))
        self.lower = value & 0x0F
        if useCycles:
            self.cpu.cycles -= 1
        
    def zFlagCompare(self, a, reset=False):
        if (reset):
             self.reset()
        if isinstance(a, (Register)):
            a = a.get()
        self.zFlag = ((a & 0xFF) == 0)
            
    def cFlagAdd(self, s, compareAnd=0x01, reset=False):
        if (reset):
             self.reset()
        if (s & compareAnd) != 0:
            self.cFlag = True

    def hFlagCompare(self, a, b):
        if isinstance(a, (Register)):
            a = a.get()
        if isinstance(b, (Register)):
            b = b.get()
        if (a & 0x0F) < (b & 0x0F):
            self.hFlag = True
            
    def cFlagCompare(self,  a, b):
        if isinstance(a, (Register)):
            a = a.get()
        if isinstance(b, (Register)):
            b = b.get()
        if a < b:
            self.cFlag = True
        
# # ------------------------------------------------------------------------------

class CPU(object):
    """
    PyBoy GameBoy (TM) Emulator
    
    Central Unit ProcessOR (Sharp LR35902 CPU)
    """
    def __init__(self, interrupt, memory):
        self.interrupt = interrupt
        self.memory = memory
        self.ime = False
        self.halted = False
        self.cycles = 0
        self.iniRegisters()
        self.rom = []
        self.reset()

    def iniRegisters(self):
        self.b = Register(self)
        self.c = Register(self)
        self.bc = DoubleRegister(self, self.b, self.c, constants.RESET_BC)
        
        self.d = Register(self)
        self.e = Register(self)
        self.de = DoubleRegister(self, self.d, self.e, constants.RESET_DE)

        self.h = Register(self)
        self.l = Register(self)
        self.hl = DoubleRegister(self, self.h, self.l, constants.RESET_HL)
        
        self.hli = ImmediatePseudoRegister(self, self.hl)
        self.pc = DoubleRegister(self, resetValue=constants.RESET_PC)
        self.sp = DoubleRegister(self, resetValue=constants.RESET_SP)
        
        self.a = Register(self, constants.RESET_A)
        self.f = FlagRegister(self)
        self.af = DoubleRegister(self, self.a, self.f)
        

    def reset(self):
        self.resetRegisters()
        self.f.reset()
        self.f.zFlag = True
        self.ime = False
        self.halted = False
        self.cycles = 0
        
    def resetRegisters(self):
        self.a.reset()
        self.f.reset()
        self.bc.reset()
        self.de.reset()
        self.hl.reset()
        self.sp.reset()
        self.pc.reset()
        
    def getAF(self):
        return self.af
        
    def getA(self):
        return self.a
    
    def getF(self):
        return self.f
        
    def getBC(self):
        return self.bc
    
    def getB(self):
        return self.b
    
    def getC(self):
        return self.c
        
    def getDE(self):
        return self.de
        
    def getD(self):
        return self.d
        
    def getE(self):
        return self.e
        
    def getHL(self):
        return self.hl
        
    def getHLi(self):
        return self.hli
        
    def getH(self):
        return self.h
        
    def getL(self):
        return self.l
             
    def getSP(self):
        return self.sp

    def getIF(self):
        val = 0x00
        if self.ime:
            val = 0x01
        if self.halted:
            val += 0x80
        return val

    def isZ(self):
        """ zero flag"""
        return self.f.zFlag

    def isC(self):
        """ carry flag, true if the result did not fit in the register"""
        return self.f.cFlag

    def isH(self):
        """ half carry, carry from bit 3 to 4"""
        return self.f.hFlag

    def isN(self):
        """ subtract flag, true if the last operation was a subtraction"""
        return self.f.nFlag
    
    def isS(self):
        return self.f.sFlag
    
    def isP(self):
        return self.f.pFlag
    
    def isNotZ(self):
        return not self.isZ()

    def isNotC(self):
        return not self.isC()
    
    def isNotH(self):
        return not self.isH()

    def isNotN(self):
        return not self.isN()

    def setROM(self, banks):
                    
        # Flags ............................................
        self.rom = banks       
            
    def emulate(self, ticks):
        self.cycles += ticks
        self.handlePendingInterrupt()
        while self.cycles > 0:
            self.execute(self.fetch())

    def handlePendingInterrupt(self):
        # Interrupts
        if self.halted:
            if self.interrupt.isPending():
                self.halted = False
                self.cycles -= 4
            elif (self.cycles > 0):
                self.cycles = 0
        if self.ime and self.interrupt.isPending():
            self.lowerPendingInterrupt()
            
    def lowerPendingInterrupt(self):
        for flag in self.interrupt.interruptFlags:
            if flag.isPending():
                self.ime = False
                self.call(flag.callCode, useCycles=False)
                flag.setPending(False)
                return

    def fetchExecute(self):
        # Execution
        FETCH_EXECUTE_OP_CODES[self.fetch()](self)
        
    def execute(self, opCode):
        OP_CODES[opCode](self)
        
    def read(self, hi, lo=None):
        # memory Access, 1 cycle
        address = hi
        if lo != None:
            address = (hi << 8) + lo
        self.cycles -= 1
        return self.memory.read(address)

    def write(self, address, data):
        # 2 cycles
        self.memory.write(address, data)
        self.cycles -= 2

    def fetch(self, useCycles=True):
        # Fetching  1 cycle
        self.cycles += 1
        if self.pc.get(useCycles) <= 0x3FFF:
            data =  self.rom[self.pc.get(useCycles)]
        else:
            data = self.memory.read(self.pc.get(useCycles))
        self.pc.inc(useCycles) # 2 cycles
        return data
    
    def fetchDoubleAddress(self):
        lo = self.fetch() # 1 cycle
        hi = self.fetch() # 1 cycle
        return (hi << 8) + lo
        
    def fetchDoubleRegister(self, register):
        self.popDoubleRegister(CPU.fetch, register)

    def push(self, data, useCycles=True):
        # Stack, 2 cycles
        self.sp.dec(useCycles) # 2 cycles
        self.memory.write(self.sp.get(useCycles), data)
        
    def pushDoubleRegister(self, register, useCycles=True):
        # PUSH rr 4 cycles
        self.push(register.getHi(), useCycles) # 2 cycles
        self.push(register.getLo(), useCycles) # 2 cycles

    def pop(self):
        # 1 cycle
        data = self.memory.read(self.sp.get())
        self.sp.inc() # 2 cycles
        self.cycles += 1
        return data
    
    def popDoubleRegister(self, getter, register=None):
        # 3 cycles
        if register == None:
            register = getter
            getter = CPU.pop
        b = getter(self) # 1 cycle
        a = getter(self) # 1 cycle
        register.set(a, b) # 2 cycles
        self.cycles += 1
        
    def call(self, address, useCycles=True):
        # 4 cycles
        self.push(self.pc.getHi(useCycles), useCycles) # 2 cycles
        self.push(self.pc.getLo(useCycles), useCycles) # 2 cycles
        self.pc.set(address, None, useCycles)       # 1 cycle
        if useCycles:
            self.cycles += 1
        
    def ld(self, getter, setter):
        # 1 cycle
        setter(getter()) # 1 cycle
        
    def loadFetchRegister(self, register):
        self.ld(self.fetch, register.set)
        
    def storeHlInPC(self):
        # LD PC,HL, 1 cycle
        self.ld(self.hl.get, self.pc.set)
        
    def fetchLoad(self, getter, setter):
        self.ld(self.fetch, setter)

    def addA(self, getter, setter=None):
        # ALU, 1 cycle
        added = (self.a.get() + getter()) & 0xFF
        self.f.zFlagCompare(added, reset=True)
        self.f.hFlagCompare(added, self.a)
        self.f.cFlagCompare(added, self.a)
        self.a.set(added) # 1 cycle
        
    def addHL(self, register):
        # 2 cycles
        added = (self.hl.get() + register.get()) & 0xFFFF # 1 cycle
        self.f.reset(keepZ=True)
        self.f.hFlagCompare((added >> 8), self.hl)
        self.f.cFlagCompare(added, self.hl)
        self.hl.set(added)
        self.cycles -= 1
        
    def addWithCarry(self, getter, setter=None):
        # 1 cycle
        data = getter()
        s = self.a.get() + data
        if self.f.cFlag:
            s +=1
        self.carryFlagFinish(s,data)

    def subtractWithCarry(self, getter, setter=None):
        # 1 cycle
        data = getter()
        s = self.a.get() - data
        if self.f.cFlag:
            s -= 1
        self.carryFlagFinish(s, data)
        self.f.nFlag = True
        
    def carryFlagFinish(self, s, data):
        self.f.reset()
        # set the hflag if the 0x10 bit was affected
        if ((s ^ self.a.get() ^ data) & 0x10) != 0:
            self.f.hFlag = True
        if s >= 0x100:
            self.f.cFlag= True
        self.f.zFlagCompare(s)
        self.a.set(s)  # 1 cycle
        
    def subtractA(self, getter, setter=None):
        # 1 cycle
        self.compareA(getter, setter) # 1 cycle
        self.a.sub(getter(useCycles=False), False)

    def fetchSubtractA(self):
        data = self.fetch()
        self.subtractA(lambda useCycles=False: data)

    def compareA(self, getter, setter=None):
        # 1 cycle
        s = (self.a.get() - getter()) & 0xFF
        self.f.reset()
        self.f.nFlag = True
        self.f.zFlagCompare(s)
        self.hcFlagFinish(s)
        self.cycles -= 1
            
    def hcFlagFinish(self, data):
        if data > self.a.get():
            self.f.cFlag = True
        self.f.hFlagCompare(self.a, data)
        
    def AND(self, getter, setter=None):
        # 1 cycle
        self.a.set(self.a.get() & getter())  # 1 cycle
        self.f.zFlagCompare(self.a, reset=True)

    def XOR(self, getter, setter=None):
        # 1 cycle
        self.a.set( self.a.get() ^ getter())  # 1 cycle
        self.f.zFlagCompare(self.a, reset=True)

    def OR(self, getter, setter=None):
        # 1 cycle
        self.a.set(self.a.get() | getter())  # 1 cycle
        self.f.zFlagCompare(self.a, reset=True)

    def incDoubleRegister(self, doubleRegister):
        doubleRegister.inc()
        
    def decDoubleRegister(self, doubleRegister):
        doubleRegister.dec()
        
    def inc(self, getter, setter):
        # 1 cycle
        data = (getter() + 1) & 0xFF
        self.decIncFlagFinish(data, setter, 0x00)
        
    def dec(self, getter, setter):
        # 1 cycle
        data = (getter() - 1) & 0xFF
        self.decIncFlagFinish(data, setter, 0x0F)
        self.f.nFlag = True
     
    def decIncFlagFinish(self, data, setter, compare):
        self.f.reset(keepC=True)
        self.f.zFlagCompare(data)
        if (data & 0x0F) == compare:
            self.f.hFlag = True
        setter(data) # 1 cycle

    def rotateLeftCircular(self, getter, setter):
        # RLC 1 cycle
        data = getter()
        s = (data  << 1) + (data >> 7)
        self.flagsAndSetterFinish(s, setter, 0x80)
        #self.cycles -= 1

    def rotateLeftCircularA(self):
        # RLCA rotateLeftCircularA 1 cycle
        self.rotateLeftCircular(self.a.get, self.a.set)

    def rotateLeft(self, getter, setter):
        # 1 cycle
        s = (getter() << 1) & 0xFF
        if self.f.cFlag:
            s += 0x01
        self.flagsAndSetterFinish(s, setter, 0x80) # 1 cycle

    def rotateLeftA(self):
        # RLA  1 cycle
        self.rotateLeft(self.a.get, self.a.set)
        
    def rotateRightCircular(self, getter, setter):
        data = getter()
        # RRC 1 cycle
        s = (data >> 1) + ((data & 0x01) << 7)
        self.flagsAndSetterFinish(s, setter) # 1 cycle
   
    def rotateRightCircularA(self):
        # RRCA 1 cycle
        self.rotateRightCircular(self.a.get, self.a.set)

    def rotateRight(self, getter, setter):
        # 1 cycle
        s = (getter() >> 1)
        if self.f.cFlag:
            s +=  0x08
        self.flagsAndSetterFinish(s, setter) # 1 cycle

    def rotateRightA(self):
        # RRA 1 cycle
        self.rotateRight(self.a.get, self.a.set)

    def shiftLeftArithmetic(self, getter, setter):
        # 2 cycles
        s = (getter() << 1) & 0xFF
        self.flagsAndSetterFinish(s, setter, 0x80) # 1 cycle

    def shiftRightArithmetic(self, getter, setter):
        data = getter()
        # 1 cycle
        s = (data >> 1) + (data & 0x80)
        self.flagsAndSetterFinish(s, setter) # 1 cycle

    def shiftWordRightLogical(self, getter, setter):
        # 2 cycles
        s = (getter() >> 1)
        self.flagsAndSetterFinish(s, setter) # 2 cycles
        
    def flagsAndSetterFinish(self, s, setter, compareAnd=0x01):
        # 2 cycles
        s &= 0xFF
        self.f.zFlagCompare(s,  reset=True)
        self.f.cFlagAdd(s, compareAnd)
        setter(s) # 1 cycle

    def swap(self, getter, setter):
        data = getter()
        # 1 cycle
        s = ((data << 4) + (data >> 4)) & 0xFF
        self.f.zFlagCompare(s, reset=True)
        setter(s)

    def testBit(self, getter, setter, n):
        # 2 cycles
        self.f.reset(keepC=True)
        self.f.hFlag = True
        self.f.zFlag = False
        if (getter() & (1 << n)) == 0:
            self.f.zFlag = True
        self.cycles -= 1

    def setBit(self, getter, setter, n):
        # 1 cycle
        setter(getter() | (1 << n)) # 1 cycle
        
    def resetBit(self, getter, setter, n):
        # 1 cycle
        setter(getter() & (~(1 << n))) # 1 cycle
        
    def storeFetchedMemoryInA(self):
        # LD A,(nnnn), 4 cycles
        self.a.set(self.read(self.fetchDoubleAddress()))  # 1+1 + 2 cycles

    def writeAAtBCAddress(self):
        # 2 cycles
        self.write(self.bc.get(), self.a.get())
        
    def writeAAtDEAddress(self):
        self.write(self.de.get(), self.a.get())
           
    def storeMemoryAtBCInA(self):
        self.a.set(self.read(self.bc.get()))

    def storeMemoryAtDEInA(self):
        self.a.set(self.read(self.de.get()))

    def ld_dbRegisteri_A(self, register):
        # LD (rr),A  2 cycles
        self.write(register.get(), self.a.get()) # 2 cycles

    def load_mem_SP(self):
        # LD (nnnn),SP  5 cycles
        address = self.fetchDoubleAddress() # 2 cycles
        self.write(address, self.sp.getLo())  # 2 cycles
        self.write((address + 1), self.sp.getHi()) # 2 cycles
        self.cycles += 1

    def storeAAtFetchedAddress(self):
        # LD (nnnn),A  4 cycles
        self.write(self.fetchDoubleAddress(), self.a.get()) # 2 cycles

    def storeMemoryAtExpandedFetchAddressInA(self):
        # LDH A,(nn) 3 cycles
        self.a.set(self.read(0xFF00 + self.fetch())) # 1+1+1 cycles
        
    def storeExpandedCinA(self):
        # LDH A,(C) 2 cycles
        self.a.set(self.read(0xFF00 + self.bc.getLo())) # 1+2 cycles
        
    def loadAndIncrement_A_HLi(self):
        # loadAndIncrement A,(HL) 2 cycles
        self.a.set(self.read(self.hl.get())) # 2 cycles
        self.hl.inc()# 2 cycles
        self.cycles += 2
        
    def loadAndDecrement_A_HLi(self):
        # loadAndDecrement A,(HL)  2 cycles
        self.a.set(self.read(self.hl.get())) # 2 cycles
        self.hl.dec() # 2 cycles
        self.cycles += 2
        
    def writeAatExpandedFetchAddress(self):
        # LDH (nn),A 3 cycles
        self.write(0xFF00 + self.fetch(), self.a.get()) # 2 + 1 cycles

    def writeAAtExpandedCAddress(self):
        # LDH (C),A 2 cycles
        self.write(0xFF00 + self.bc.getLo(), self.a.get()) # 2 cycles
        
    def loadAndIncrement_HLi_A(self):
        # loadAndIncrement (HL),A 2 cycles
        self.write(self.hl.get(), self.a.get()) # 2 cycles
        self.hl.inc() # 2 cycles
        self.cycles += 2

    def loadAndDecrement_HLi_A(self):
        # loadAndDecrement (HL),A  2 cycles
        self.write(self.hl.get(), self.a.get()) # 2 cycles
        self.hl.dec() # 2 cycles
        self.cycles += 2

    def storeHlInSp(self):
        # LD SP,HL 2 cycles
        self.sp.set(self.hl.get()) # 1 cycle
        self.cycles -= 1

    def complementA(self):
        # CPA
        self.a.set(self.a.get() ^ 0xFF)
        self.f.nFlag = True
        self.f.hFlag = True

    def decimalAdjustAccumulator(self):
        # DAA 1 cycle
        delta = 0
        if self.isH(): 
            delta |= 0x06
        if self.isC():
            delta |= 0x60
        if (self.a.get() & 0x0F) > 0x09:
            delta |= 0x06
            if (self.a.get() & 0xF0) > 0x80:
                delta |= 0x60
        if (self.a.get() & 0xF0) > 0x90:
            delta |= 0x60
        if not self.isN():
            self.a.set((self.a.get() + delta) & 0xFF) # 1 cycle
        else:
            self.a.set((self.a.get() - delta) & 0xFF) # 1 cycle
        self.f.reset(keepN=True)
        if delta >= 0x60:
            self.f.cFlag = True
        self.f.zFlagCompare(self.a)

    def incDoubleRegister(self, register):
        # INC rr
        register.inc()

    def decDoubleRegister(self, register):
        # DEC rr
        register.dec()

    def incrementSPByFetch(self):
        # ADD SP,nn 4 cycles
        self.sp.set(self.getFetchAddedSP()) # 1+1 cycle
        self.cycles -= 2

    def storeFetchAddedSPInHL(self):
        # LD HL,SP+nn   3  cycles
        self.hl.set(self.getFetchAddedSP()) # 1+1 cycle
        self.cycles -= 1

    def getFetchAddedSP(self):
        # 1 cycle
        offset = self.fetch() # 1 cycle
        s = (self.sp.get() + offset) & 0xFFFF
        self.f.reset()
        if (offset >= 0):
            if s < self.sp.get():
                self.f.cFlag = True
            if (s & 0x0F00) < (self.sp.get() & 0x0F00):
                self.f.hFlag = True
        else:
            if s > self.sp.get():
                self.f.cFlag = True
            if (s & 0x0F00) > (self.sp.get() & 0x0F00):
                self.f.hFlag = True
        return s

    def complementCarryFlag(self):
        # CCF/SCF
        self.f.reset(keepZ=True, keepC=True)
        self.f.cFlag = not self.f.cFlag

    def setCarryFlag(self):
        self.f.reset(keepZ=True)
        self.f.cFlag = True

    def nop(self):
        # NOP 1 cycle
        self.cycles -= 1

    def unconditionalJump(self):
        # JP nnnn, 4 cycles
        self.pc.set(self.fetchDoubleAddress()) # 1+2 cycles
        self.cycles -= 1

    def conditionalJump(self, cc):
        # JP cc,nnnn 3,4 cycles
        if cc:
            self.unconditionalJump() # 4 cycles
        else:
            self.pc.add(2) # 3 cycles

    def relativeUnconditionalJump(self):
        # JR +nn, 3 cycles
        self.pc.add(self.fetch()) # 3 + 1 cycles
        self.cycles += 1

    def relativeConditionalJump(self, cc):
        # JR cc,+nn, 2,3 cycles
        if cc:
            self.relativeUnconditionalJump() # 3 cycles
        else:
            self.pc.inc() # 2 cycles
    
    def unconditionalCall(self):
        # CALL nnnn, 6 cycles
        self.call(self.fetchDoubleAddress())  # 4+2 cycles

    def conditionalCall(self, cc):
        # CALL cc,nnnn, 3,6 cycles
        if cc:
            self.unconditionalCall() # 6 cycles
        else:
            self.pc.add(2) # 3 cycles

    def ret(self):
        # RET 4 cycles
        lo = self.pop() # 1 cycle
        hi = self.pop() # 1 cycle
        self.pc.set(hi, lo) # 2 cycles

    def conditionalReturn(self, cc):
        # RET cc 2,5 cycles
        if cc:
            self.ret() # 4 cycles
            # FIXME maybe this should be the same
            self.cycles -= 1
        else:
            self.cycles -= 2

    def returnFormInterrupt(self):
        # RETI 4 cycles
        self.ret() # 4 cycles
        self.enableInterrupts() # 1 cycle + others
        self.cycles += 1

    def restart(self, nn):
        # RST nn 4 cycles
        self.call(nn) # 4 cycles

    def disableInterrupts(self):
        # DI/EI 1 cycle
        self.ime = False
        self.cycles -= 1

    def enableInterrupts(self):
        # 1 cycle
        self.ime = True
        self.execute(self.fetch()) #  1
        self.handlePendingInterrupt()

    def halt(self):
        # HALT/STOP
        self.halted = True
        # emulate bug when interrupts are pending
        if (not self.ime and self.interrupt.isPending()):
            self.execute(self.memory.read(self.pc.get()))
        self.handlePendingInterrupt()

    def stop(self):
        # 0 cycles
        self.cycles += 1
        self.fetch()

# ------------------------------------------------------------------------------
# OPCODE LOOKUP TABLE GENERATION -----------------------------------------------


GROUPED_REGISTERS = (CPU.getB, CPU.getC, CPU.getD, CPU.getE, CPU.getH, CPU.getL, CPU.getHLi, CPU.getA)

def create_group_op_codes(table):
    opCodes =[]
    for entry in table:
        opCode   = entry[0]
        step     = entry[1]
        function = entry[2]
        if len(entry) == 4:
            for registerGetter in GROUPED_REGISTERS:
                for n in entry[3]:
                    opCodes.append((opCode, group_lambda(function, registerGetter, n)))
                    opCode += step
        if len(entry) == 5:
            entryStep = entry[4]
            for registerGetter in GROUPED_REGISTERS:
                stepOpCode = opCode
                for n in entry[3]:
                    opCodes.append((stepOpCode, group_lambda(function, registerGetter, n)))
                    stepOpCode += entryStep
                opCode+=step
        else:
            for registerGetter in GROUPED_REGISTERS:
                opCodes.append((opCode,group_lambda(function, registerGetter)))
                opCode += step
    return opCodes

def group_lambda(function, registerGetter, value=None):
    if value == None:
        return lambda s: function(s, registerGetter(s).get, registerGetter(s).set)
    else:
        return  lambda s: function(s, registerGetter(s).get, registerGetter(s).set, value)


def create_load_group_op_codes():
    opCodes = []
    opCode  = 0x40
    for storeRegister in GROUPED_REGISTERS:
        for loadRegister in GROUPED_REGISTERS:
            if loadRegister != CPU.getHLi or storeRegister != CPU.getHLi:
                opCodes.append((opCode, load_group_lambda(storeRegister, loadRegister)))
            opCode += 1
    return opCodes
            
def load_group_lambda(storeRegister, loadRegister):
        return lambda s: CPU.ld(s, loadRegister(s).get, storeRegister(s).set)
    
    
def create_register_op_codes(table):
    opCodes = []
    for entry in table:
        opCode   = entry[0]
        step     = entry[1]
        function = entry[2]
        for registerOrGetter in entry[3]:
            opCodes.append((opCode, register_lambda(function, registerOrGetter)))
            opCode += step
    return opCodes

def register_lambda(function, registerOrGetter):
    if callable(registerOrGetter):
        return lambda s: function(s, registerOrGetter(s))
    else:
        return lambda s: function(s, registerOrGetter)
        
        
def initialize_op_code_table(table):
    result = [None] * (0xFF+1)
    for entry in  table:
        if (entry is None) or (len(entry) == 0) or entry[-1] is None:
            continue
        if len(entry) == 2:
            positions = [entry[0]]
        else:
            positions = range(entry[0], entry[1]+1)
        for pos in positions:
            result[pos] = entry[-1]
    return result

# OPCODE TABLES ---------------------------------------------------------------
                        
FIRST_ORDER_OP_CODES = [
    (0x00, CPU.nop),
    (0x08, CPU.load_mem_SP),
    (0x10, CPU.stop),
    (0x18, CPU.relativeUnconditionalJump),
    (0x02, CPU.writeAAtBCAddress),
    (0x12, CPU.writeAAtDEAddress),
    (0x22, CPU.loadAndIncrement_HLi_A),
    (0x32, CPU.loadAndDecrement_HLi_A),
    (0x0A, CPU.storeMemoryAtBCInA),
    (0x1A, CPU.storeMemoryAtDEInA),
    (0x2A, CPU.loadAndIncrement_A_HLi),
    (0x3A, CPU.loadAndDecrement_A_HLi),
    (0x07, CPU.rotateLeftCircularA),
    (0x0F, CPU.rotateRightCircularA),
    (0x17, CPU.rotateLeftA),
    (0x1F, CPU.rotateRightA),
    (0x27, CPU.decimalAdjustAccumulator),
    (0x2F, CPU.complementA),
    (0x37, CPU.setCarryFlag),
    (0x3F, CPU.complementCarryFlag),
    (0x76, CPU.halt),
    (0xF3, CPU.disableInterrupts),
    (0xFB, CPU.enableInterrupts),
    (0xE2, CPU.writeAAtExpandedCAddress),
    (0xEA, CPU.storeAAtFetchedAddress),
    (0xF2, CPU.storeExpandedCinA),
    (0xFA, CPU.storeFetchedMemoryInA),
    (0xC3, CPU.unconditionalJump),
    (0xC9, CPU.ret),
    (0xD9, CPU.returnFormInterrupt),
    (0xE9, CPU.storeHlInPC),
    (0xF9, CPU.storeHlInSp),
    (0xE0, CPU.writeAatExpandedFetchAddress),
    (0xE8, CPU.incrementSPByFetch),
    (0xF0, CPU.storeMemoryAtExpandedFetchAddressInA),
    (0xF8, CPU.storeFetchAddedSPInHL),
    (0xCB, CPU.fetchExecute),
    (0xCD, CPU.unconditionalCall),
    (0xC6, lambda s: CPU.addA(s, s.fetch)),
    (0xCE, lambda s: CPU.addWithCarry(s,  s.fetch)),
    (0xD6, CPU.fetchSubtractA),
    (0xDE, lambda s: CPU.subtractWithCarry(s,  s.fetch)),
    (0xE6, lambda s: CPU.AND(s,  s.fetch)),
    (0xEE, lambda s: CPU.XOR(s,  s.fetch)),
    (0xF6, lambda s: CPU.OR(s,   s.fetch)),
    (0xFE, lambda s: CPU.compareA(s,  s.fetch)),
    (0xC7, lambda s: CPU.restart(s, 0x00)),
    (0xCF, lambda s: CPU.restart(s, 0x08)),
    (0xD7, lambda s: CPU.restart(s, 0x10)),
    (0xDF, lambda s: CPU.restart(s, 0x18)),
    (0xE7, lambda s: CPU.restart(s, 0x20)),
    (0xEF, lambda s: CPU.restart(s, 0x28)),
    (0xF7, lambda s: CPU.restart(s, 0x30)),
    (0xFF, lambda s: CPU.restart(s, 0x38)),
]

REGISTER_GROUP_OP_CODES = [
    (0x04, 0x08, CPU.inc),
    (0x05, 0x08, CPU.dec),    
    (0x06, 0x08, CPU.loadFetchRegister),
    (0x80, 0x01, CPU.addA),    
    (0x88, 0x01, CPU.addWithCarry),    
    (0x90, 0x01, CPU.subtractA),    
    (0x98, 0x01, CPU.subtractWithCarry),    
    (0xA0, 0x01, CPU.AND),    
    (0xA8, 0x01, CPU.XOR),    
    (0xB0, 0x01, CPU.OR),
    (0xB8, 0x01, CPU.compareA),
    (0x06, 0x08, CPU.fetchLoad)
]    
        

REGISTER_SET_A = [CPU.getBC, CPU.getDE, CPU.getHL, CPU.getSP]
REGISTER_SET_B = [CPU.getBC, CPU.getDE, CPU.getHL, CPU.getAF]
FLAG_REGISTER_SET = [CPU.isNotZ, CPU.isZ, CPU.isNotC, CPU.isC]
REGISTER_OP_CODES = [ 
    (0x01, 0x10, CPU.fetchDoubleRegister,     REGISTER_SET_A),
    (0x09, 0x10, CPU.addHL,                   REGISTER_SET_A),
    (0x03, 0x10, CPU.incDoubleRegister,       REGISTER_SET_A),
    (0x0B, 0x10, CPU.decDoubleRegister,       REGISTER_SET_A),
    (0xC0, 0x08, CPU.conditionalReturn,       FLAG_REGISTER_SET),
    (0xC2, 0x08, CPU.conditionalJump,         FLAG_REGISTER_SET),
    (0xC4, 0x08, CPU.conditionalCall,         FLAG_REGISTER_SET),
    (0x20, 0x08, CPU.relativeConditionalJump, FLAG_REGISTER_SET),
    (0xC1, 0x10, CPU.popDoubleRegister,       REGISTER_SET_B),
    (0xC5, 0x10, CPU.pushDoubleRegister,      REGISTER_SET_B)
]

SECOND_ORDER_REGISTER_GROUP_OP_CODES = [
    (0x00, 0x01, CPU.rotateLeftCircular),    
    (0x08, 0x01, CPU.rotateRightCircular),    
    (0x10, 0x01, CPU.rotateLeft),    
    (0x18, 0x01, CPU.rotateRight),    
    (0x20, 0x01, CPU.shiftLeftArithmetic),    
    (0x28, 0x01, CPU.shiftRightArithmetic),    
    (0x30, 0x01, CPU.swap),    
    (0x38, 0x01, CPU.shiftWordRightLogical),
    (0x40, 0x01, CPU.testBit,  range(0, 8), 0x08),    
    (0xC0, 0x01, CPU.setBit,   range(0, 8), 0x08),
    (0x80, 0x01, CPU.resetBit, range(0, 8), 0x08)         
]

# RAW OPCODE TABLE INITIALIZATION ----------------------------------------------

FIRST_ORDER_OP_CODES += create_register_op_codes(REGISTER_OP_CODES)
FIRST_ORDER_OP_CODES += create_group_op_codes(REGISTER_GROUP_OP_CODES)
FIRST_ORDER_OP_CODES += create_load_group_op_codes()
SECOND_ORDER_OP_CODES = create_group_op_codes(SECOND_ORDER_REGISTER_GROUP_OP_CODES)


OP_CODES = initialize_op_code_table(FIRST_ORDER_OP_CODES)
FETCH_EXECUTE_OP_CODES = initialize_op_code_table(SECOND_ORDER_OP_CODES)
