#!/usr/bin/pyton
# encoding: utf-8
# tested with: Ghostscript 9.05, GNU barcode 0.98, ImageMagick 6.7.8.2, Python 2.7.3

import os
import math
import random
import tempfile

BAROFFX=64
BAROFFY=60
BARHEIGHT=294
SETWIDTH=5
BARGEN='barcode -e ean -b %(code)s -g 534x300+10+470 | gs -r70x70 -sDEVICE=tiffcrle -sOutputFile=%(tmp)s.tif -'
BARCROP='570x365'
TEXT='-pointsize 20 -font /usr/share/fonts/ttf/ms/tahoma.ttf -gravity center -draw "text 0,-160 \'%s\'" -gravity NorthWest'
COLTEXT="blue"
COLSEL="green"
COLSIX="red"
COLSIX2="#BB3300"
COLBARGRAY="#777777"

SETAB = { 
        '0':'AAAAAA',
        '1':'AABABB',
        '2':'AABBAB',
        '3':'AABBBA',
        '4':'ABAABB',
        '5':'ABBAAB',
        '6':'ABBBAA',
        '7':'ABABAB',
        '8':'ABABBA',
        '9':'ABBABA'}

def randcode():
    return ''.join(str(random.randint(0, 9)) for i in range(12))

def irepl(s,index, char):
    z = list(s)
    z[index] = char
    return ''.join(z)

class IM(object):
    def __init__(self):
        self.clist = []
        self.tmp = tempfile.mkstemp()[1]
        self.cmd = 'convert'
    def cmadd(self, cmd):
        self.cmd += ' ' + cmd
    def exc(self, cmd=None):
        if not cmd:
            cmd = self.cmd
        if os.system(cmd) != 0:
            raise Exception('Failed: %s' % cmd)
    def build(self, ext='gif'):
        self.clist.append(ext)
        self.name = "%s.%s" % (self.tmp, ext)
        self.cmadd(self.name)
        self.exc()
        return self
    def show(self):
        self.exc('/usr/lib/kde3/bin/gwenview %s.gif &' % self.tmp )
        return self
    def clean(self):
        for f in self.clist:
            os.remove('%s.%s' % (self.tmp, f))

class CodeFrame(IM):
    def __init__(self, code):
        super(CodeFrame, self).__init__()
        self.code = code
        self.exc(BARGEN % {'code':code, 'tmp':self.tmp})
        self.clist.append('tif')
        self.cmadd('%s.tif -extent %s' % (self.tmp, BARCROP))
    def info(self, text, color=COLTEXT):
        self.cmadd('-fill %s' % color)
        self.cmadd(TEXT % text)
        return self
    def fill(self, area, color):
        if isinstance(area, str):
            area = (area,)
        for a in area:
            self.cmadd('-region %s -fill "%s" -opaque black -region %s' % (a, color,  BARCROP))
        return self
    def select(self, n, color=COLSEL):
        n = n-1
        self.fill('%sx%s+%s+%s' % (SETWIDTH*7, BARHEIGHT,
            BAROFFX + SETWIDTH*(n*7+3) + (n/6)*SETWIDTH*5, BAROFFY), color )
        return self
    def cnt(self):
        s1, s2 = 0, 0
        for i, n in enumerate(self.code):
            if i%2:
                s1 += int(n)
            else:
                s2 += int(n)
        return (9 - ((s1*3+s2) % 10-1))%10
    def select_sx(self, control=True, color=COLSIX):
        if control and (self.cnt() == 6):
            self.select(12, color)
        for i in range(12):
            if i>0 and self.code[i]=='6':
                n = int(i)
                if not(i < 7 and SETAB [self.code[0]][i-1]=='A'):
                    x = n - 5*(n/5)
                    self.select(i, color)
        return self
    def select_gb(self, color=COLSIX):
        pw = { 'w3':SETWIDTH*3, 'w5':SETWIDTH*5, 'h':BARHEIGHT, 'y':BAROFFY,
                'g1':BAROFFX, 'g2':BAROFFX + SETWIDTH*(3+7*6), 'g3':BAROFFX + SETWIDTH*(3+5+7*12)  }
        self.fill((
            '%(w3)sx%(h)s+%(g1)s+%(y)s' % pw, 
            '%(w5)sx%(h)s+%(g2)s+%(y)s' % pw, 
            '%(w3)sx%(h)s+%(g3)s+%(y)s' % pw), color)
        return self
    def select_gr(self):
        for i in range(12):
            col = 50 + int(150*(i/11.0)  )
            if i%2:
                col = "#777780"
            else:
                col = "#778077"
            self.select(i+1, col) 
        return self
    def build(self, ext='gif'):
        return super(CodeFrame, self).build(ext)

class Animator (IM):
    def __init__(self, delay, name=None, frames=None):
        super(Animator, self).__init__()
        self.clist = []
        if name:
            self.tmp = name
        else:
            self.tmp = tempfile.mkstemp()[1]
        self.cmadd ('-loop 0 -delay %s' % (delay))
        if frames:
            self.add(frames)
    def add(self, frame):
        if isinstance(frame, IM):
            frame=(frame,)
        for f in frame:
            self.clist.append(f)
            self.cmadd(f.name)


def basecode(n=None):
    if n is None:
        return '000000000000'
    if n - 5*(n/5) < 3:
        return '600000000000'
    else:
        return '400000000000'

def cf1(text, n, code, seta=False):
    x = n - 5*(n/5)
    code = irepl( irepl(code, x+2, str(n)), x+7, str(n))
    return CodeFrame(code).info(text).select_gb().select_sx(False).select(
            x+2).select(x+7).select_gr().build()


b = Animator(25, "ean13vis-rnd")
for i in range(38):
    b.add(CodeFrame(randcode()).info("Случайная выборка / Random sample").select_gb(
        'rgb(%s, 25, 0)' % int( 155+100*(math.fabs(math.sin(float(i)/4))) )
        ).select_sx(True, COLSIX2).select_gr().build())
b.build().show()

a = Animator(150, "ean13vis-set")
for i in range(10):
    a.add( cf1("Набор B (SET B) / Набор C (SET C)", i, basecode(i)))
for i in range(10):
    a.add(cf1("Набор A (SET A) / Набор C (SET C)", i, basecode(), True))
a.build().show()
