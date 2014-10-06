from libs.mysql import *
from collections import defaultdict
import glob, os, sys, time
from libs.mywebutil import url_read, url_exists, getIP
from libs.myemail import Email, URL_BASE, fromaddr, READER_PWD
from libs.mydateutil import DATE_STRING, today_ymd
from pyPdf import PdfFileWriter, PdfFileReader
from libs.TerceraDefs import RECIPIENTES, LISTA_TOKENS
#####################################################
MAXIMUM_NUMBER_OF_PAGES = 150       # aumentado el 30/08/2014
OUT_FILENAME = "TERCERA/diario-%d%02d%02d.pdf" #anyo-mes-dia
# DO ME SOON: parse new keywords (only)
#####################################################
def Sports():
    data = sqlget("SELECT DATE, PAGE FROM TOKENS WHERE TOKEN='DESTACADOS EN TV'")
    for row in data:
        fecha, pageNumber = row
        a,m,d = [int(fi) for fi in str(fecha).split('-')]
        page_text = GetText(GetPage(a,m,d,pageNumber))
        where = page_text.index('Deportes')
        print fecha, page_text[where-20:where+100]
#####################################################
def GetPage(anyo,mes,dia,page):
    link = URL_BASE %(anyo,mes,dia,page)
    #if url_exists(link):
    try:
        x = url_read(link)
    #else:
    except:
		x = None
    return x
#####################################################
def DB_Parse(anyo,mes,dia,pagen0):
    date_string = DATE_STRING %(anyo,mes,dia)
    page = dumpundump(GetPage(anyo,mes,dia,pagen0)).extractText()
    SplitInsert(page, date_string, pagen0)
#####################################################
def SeeBig():
    print sqlget("SELECT TOKEN, NUMBER FROM BIGTOKENS ORDER BY NUMBER DESC LIMIT 5")
#####################################################
def ReadPaper(anyo,mes,dia):
	filename = OUT_FILENAME %(anyo,mes,dia)
	pdf = PdfFileReader(open(filename,"rb"))
	return pdf
#####################################################
def	ReadIt():
	y,m,d = today_ymd()
	cmd = OUT_FILENAME %(y,m,d)
	os.popen(cmd).read()
#####################################################
def GetMonthOfPapers(anyo,mes):
	for dia in xrange(1,31):
		GetPaper(anyo,mes,dia)
#####################################################
def Find_Treasure(what):
	filelist = glob.glob("DUMPED\\page*.pdf")
	for file in filelist:
		input = PdfFileReader(open(file, 'rb'))
		page = input.getPage(0)
		text = page.extractText()

		if what in text:
			where = text.find(what)
			pageNumber = file[10:14]
			print "PAGE %s: %s" %(pageNumber, text[where:where+20])
#####################################################
def dump(thisPage):
	f = open("DATA/dump","wb")
	f.write(thisPage)
	f.close()
#####################################################
def undump():
    data = open("DATA/dump","rb")
    return data
#####################################################
class pdf():
    def __init__(self, anyo,mes,dia):
        self.fileout = OUT_FILENAME %(anyo,mes,dia)
        self.output = PdfFileWriter()
    def __add__(self, page):
        self.output.addPage(page)
	def save(self):
	    outputStream = file(self.fileout, "wb")
	    self.output.write(outputStream)
	    outputStream.close()
        self.nReadPages = PdfFileReader(file(self.fileout,'rb')).numPages
#####################################################
def pdf_write(output, filename):
	outputStream = file(filename, "wb")
	output.write(outputStream)
	outputStream.close()
#####################################################
def dumpundump(thisPage):
	dump(thisPage)
	pdfReader = PdfFileReader(undump())
	pagePDF = pdfReader.getPage(0)
	return pagePDF
#####################################################
class TokenInsert():
    def __init__(self, table):
        self.table = table
        print "initialized insertion class of table %s" %(table)
        self.limit = 50
        self.size = 0
        self.container = []
        self.varnames = {'BIGTOKENS': '(DATE,TOKEN,NUMBER,PAGE)',}
        self.vars = self.varnames[self.table]

    def __add__(self, tokendata):
        self.container.append(tokendata)
        #print self.container
        self.size+=1
        if self.size == self.limit:     # the shit has hit the fan
            self.insert()
        return self

    def insert(self):
        sqlq = "INSERT INTO %s %s VALUES " %(self.table, self.vars)
        for tokendata in self.container:
            print tokendata
            sqlq += "('%s','%s',%d,%d)" %(tokendata)
        sql(sqlq)
        self.container = []
        self.size=0

class reader():
    def __init__(self, *args):        # formatos: None, (token, debug), date
        if args is None:
            print "NONE"
        self.debugging = False
        self.token = 'DESTACADOS EN TV'     # by default, read DEPORTES for today
        self.send_email = True
        anyo, mes, dia = today_ymd()
        print len(args)
        if 'debug' in args:
            print 'DEBUGGING MODE'
            self.debugging = True
        if 'EMPRENDEDOR' in args:
            self.token = 'EMPRENDEDOR'
        if len(args)>2: #specifying date
            anyo, mes, dia = args

        self.anyo, self.mes, self.dia = anyo,mes,dia
        self.date_string = DATE_STRING %(anyo,mes,dia)
        print "Reading %s for %s" %(self.token, self.date_string)
        self.t0 = time.time()
        self.nReadPages = 0
        self.dma = (dia,mes,anyo)

    def GetMessage(self):
        # TODO: [1] add rojadirecta links to "relevant" games
        link = URL_BASE %(self.anyo, self.mes, self.dia, self.page_n0)
        base = "%s EN PAGINA %d" %(self.token, self.page_n0)
        self.msg = "%s\n %s\n" %(base, link)
        self.runtime = int((time.time()-self.t0)/60)
        if 1<0:
            self.msg += "Un computador en algun lugar del mundo (%s) leyo el \
                diario de hoy %s en poco mas de %d minutos para hacerte \
                la vida mas facil" %(getIP(),self.date_string, runtime)

    def read(self):
        self.send_email = True
#        ReviewPaper(self.anyo, self.mes, self.dia)      # now inserts TOKENS!

        # import pdb; pdb.set_trace()
        ClearDate(self.date_string)
    	nReadPages = 0
    	page_n0 = 1
#        sql("SET SESSION max_allowed_packet=104857600")
    	while page_n0 <=MAXIMUM_NUMBER_OF_PAGES:
    		print page_n0,
    		thisPage = GetPage(self.anyo,self.mes,self.dia,page_n0)
    		if thisPage is not None:
    			nReadPages +=1
    			#pagePDF = dumpundump(thisPage)
    			#textpage = pagePDF.extractText()
    			textpage = GetText(thisPage)    # not using the intermediate result
    			for token in LISTA_TOKENS:
    				if token in textpage:
    					print  "%s EN PAGINA %d" %(token, page_n0)
    					token_insert(self.date_string,token,page_n0)
				#SplitInsert(textpage, self.date_string, page_n0)    # must use bigtoken insertion class, limit=32K?
    		page_n0 += 1
    	print "[%s] read %d pages in %d secs" %(self.date_string, nReadPages, time.time()-self.t0)

    def EnviarPublicacion(self):
        nPagina_Deportes = TokenView('DESTACADOS EN TV', self.date_string)
        nPagina_Cultura = TokenView(['Sociedad','Cultura'], self.date_string)
        print nPagina_Deportes, nPagina_Cultura
        if nPagina_Deportes is None:
            body_of_email = "CULTURA: "+ URL_BASE %(self.anyo,self.mes,self.dia,nPagina_Cultura)
        else:
            body_of_email = "DEPORTES: " + URL_BASE %(self.anyo,self.mes,self.dia, nPagina_Deportes)
            body_of_email += "<BR>CULTURA: "+ URL_BASE %(self.anyo,self.mes,self.dia,nPagina_Cultura)

        if self.send_email:
            Email(RECIPIENTES, body_of_email, self.dma)

    	self.runtime = time.time()-self.t0
        print "[%s] read %d pages in %d secs" %(self.date_string, self.nReadPages, self.runtime)
######################################################
def dumpread(thisPage): # could go to memory, faster?
    dump(thisPage)
    pdfReader = PdfFileReader(undump())
    pagePDF = pdfReader.getPage(0)
    return pagePDF

def ClassyGetPaper(passed_args=None):
    if passed_args is None:
        ThisReader = reader()
    else:
        ThisReader = reader(*passed_args)
    ThisReader.read()
    ThisReader.EnviarPublicacion()

def JustRead(passed_args=None):
    if passed_args is None: #LEARN TO USE OPTIONS_PARSER
        ThisReader = reader()
    else:
        ThisReader = reader(*passed_args)
    ThisReader.read()
#####################################################
def SplitInsert(page, date_string, pagen0):
    split_page = page.split(' ')
    print "page %d has %d words" %(pagen0, len(split_page))

    # summarize and insert
    out = defaultdict(int)
    for word in split_page:
        out[word]+=1
    exception_list = [" ",]
    t0 = time.time()
    split_ins = TokenInsert('BIGTOKENS')
    for word, word_freq in out.iteritems():
        if word not in exception_list:
            split_ins += (date_string, word, word_freq, pagen0)
    split_ins.insert()  # don't forget your doggy bag!
    print "Insertion of %d tokens in %d secs" %(len(out), time.time()-t0)
######################################################
def ClearDate(date2clear):
    sql("DELETE FROM TOKENS WHERE DATE='%s'" %(date2clear))
######################################################
def GetText(thisPage):
    pagePDF = dumpundump(thisPage)
    return pagePDF.extractText()
######################################################
#def ReviewPaper(anyo,mes,dia):
#####################################################
if __name__=="__main__":        # use python options parser
    if len(sys.argv)>1:
        ClassyGetPaper(sys.argv[1:])
    else:
        ClassyGetPaper()