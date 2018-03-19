import yobit_api, json, time, requests, datetime, mysql.connector,socket, sys

maincurr = 'usd'  # usd
currency = 'ltc'  # doge, eth
par = currency + '_' + maincurr
interest = ('doge', 'usd')
yobit_key = 'key'
yobit_secret_key = 'secret'
run = True
vklad = 0.3  # kolik dat na jeden obchod z celkoveho mnozstvi
provize = 0.004  # obvykle yobit ma 0,2%, coz je 0.002 , ja tu mam 0.004, kde tedy chci mit i ja 0.2% :)
rozhodcibod = 0.01  # 0.01 je 1 procento - kdy uskutecnit obchod kdyz se kurz zmeni o toto
# pristup do databaze
db = "kakabot"
uzivatel = "kakabot"
heslo = "kvtd2qBd8W1Qcols"
server = "127.0.0.1"

# promenne pro muj algoritmus
stav = 'nic'
stavlast = 'nic'
ccactual = 0.00
cclast = 0.00
ccpoint = 0.00
ccstart = 0.0
plus = 0  # zvysovat hodnoty kdyz se opakuje prodej prodej, nebo nakup nakup po sobe pro vice nakupu/prodeje
nakuppri=0.00  # abych neprodal levn2ji, nez nakoupil
prodejpri=0.00  # abych nekoupil draz, nez prodal
maincurrvol = 0.00  # nacte z penezenky
currencyvol = 0.00  # nacte z penezenky

def aktivni_obchody(menovypar,co): #doge_usd, buy/sell
    link = "https://yobit.net/api/3/depth/" + menovypar + "?limit=10"
    f = requests.get(link)
    print(f.json().get(par))
    nabidky = f.json().get(par).get('asks')
    poptavky = f.json().get(par).get('bids')
    if co == "buy" or co == "nakup":
        return nabidky
    if co == "sell" or co == "prodej":
        return poptavky
    else:
        return "NO"

def penezenka():
    for currency, count in wallet.items():
        if True:  # (currency in interest)
            if (currency != maincurr):
                hodnota = yobit_api.PublicApi().get_pair_ticker(par)
                print(currency.upper(), count, "prumer >" + str(hodnota.get('avg')) + " aktualne >" + str(hodnota.get('last')) + " nakup >" + str(hodnota.get('buy')) + " prodej >" + str(hodnota.get('sell')))

def actvol():  # naplni  maincurrvol a currencyvol stavem z penezenky
    global maincurrvol, currencyvol
    dotaz = yobit_api.TradeApi(key=yobit_key, secret_key=yobit_secret_key).get_info()  # penezenky a stavy v json
    account = dotaz.get('return')
    wallet = account.get('funds')
    for mena, count in wallet.items():
        if (mena == maincurr):
            maincurrvol = count
        if (mena == currency):
            currencyvol = count
    print(currency + " >> " + str(currencyvol) + " : " + maincurr + " >> " + str(maincurrvol) + " .")

def nacti():  # nacte hodnotu cc
    global ccpoint, ccactual, ccstart
    hodnota = yobit_api.PublicApi().get_pair_ticker(pair=par)
    ccactual = hodnota.get('last')
    # {'high': 603.3402, 'low': 481.50898705,
    # 'avg': 542.42459352, 'vol': 566012.01104146, 'vol_cur': 1082.91016055,
    # 'last': 532.42971141, 'buy': 530.92620723, 'sell': 532.42971141, 'updated': 1521406380}
    if (ccpoint == 0):  # prvotni nastaveni ccpoint
        ccpoint = ccactual
        ccstart = ccactual

    # link = "https://yobit.net/api/3/depth/" + par + "?limit=10"
    # usd = 0
    # f = requests.get(link)
    # nabidky = f.json().get(par).get('asks')
    # poptavky = f.json().get(par).get('bids')
    # print("Nabidky - ostatni prodavaji")
    # for nabidka in nabidky:
    #    usd += nabidka[0] * nabidka[1]
    #   print(nabidka[0], " kusu> ", nabidka[1], "za ", nabidka[0] * nabidka[1], "USD", )
    # print("Celkem za ", usd)

    # for poptavka in poptavky:
    #    usd += poptavka[0] * poptavka[1]
    #    print(poptavka[0], " kusu> ", poptavka[1], "za ", poptavka[0] * poptavka[1], "USD", )
    # print("Celkem za ", usd)

def zapis(*s):
    file = open("log_" + par + ".txt", "a")
    for i in s:
        print(i)
        file.write(i)
    print(sestav_vetu())
    file.write(sestav_vetu())
    file.close()
    ccpoint = ccactual
    stav = "nic"
    plus = 0

def sql_obchod(kolik):
    global ccactual, stav, maincurr, currency
    cnx = mysql.connector.connect(user=uzivatel, password=heslo, host=server, database=db)
    x = cnx.cursor()
    veta = "insert into kakabot.kakabot(cas, maincurr, currency, stav, kurz, kolik, kdo) values('"
    veta += str(datetime.datetime.now()) + "', '" + maincurr + "', '" + currency + "', '" + stav + "',"
    veta += str(ccactual) + "," + str(kolik) + ",'" + socket.gethostname()  + "')"
    print(veta)
    try:
        x.execute(veta)
        cnx.commit()
    except:
        cnx.rollback()


def sql_posledni(s):
    global maincurr,currency
    jmeno = socket.gethostname()
    cnx = mysql.connector.connect(user=uzivatel, password=heslo, host=server, database=db)
    x = cnx.cursor()
    try:
        x.execute("select kurz from kakabot.kakabot where maincurr= '" + maincurr + "' and currency= '" + currency + "' and stav= '" + s +"' and kdo = '" + jmeno + "' order by id desc limit 1")
        return x.fetchone()[0]
    except:
        return 0
    cnx.close()

def sql_last_stav():
    global maincurr, currency
    jmeno = socket.gethostname()
    cnx = mysql.connector.connect(user=uzivatel, password=heslo, host=server, database=db)
    x = cnx.cursor()
    try:
        x.execute("select stav from kakabot.kakabot where  maincurr= '" + maincurr + "' and currency= '" + currency + "' and kdo = '" + jmeno + "' order by id desc limit 1")
        return x.fetchone()[0]
    except:
        return 'nic'
    cnx.close()


def sestav_vetu():
    global ccpoint, ccactual, cclast, stav, plus
    text = str(datetime.datetime.now()) + " : " + par + " Point: " + str(ccpoint) + " last: " + str(cclast) + " actual: " + str(ccactual) + " Stav >" + stav + "< plus:>" + str(plus) + "<\n"
    return text

# zacatek programu - nacteme udaje z penezenky a kouknem za kolik jsme naposled nakoupili a prodali
actvol()
nakuppri=sql_posledni("nakup")
prodejpri=sql_posledni("prodej")
stavlast=sql_last_stav()
print("posledni nakup>" + str(nakuppri))
print("posledni prodej>" + str(prodejpri))
"""if ccactual > prodejpri:
    # aktualni kurz je vys nez pri poslednim prodeji, radeji nic nedelat
if ccactual < nakuppri:
    # kurz je niz nez pri poslednim nakupu radeji nic nedelat
if ccactual < prodejpri and ccactual > nakuppri:
    # kurz je mezi nakupem a prodejem
"""
vloz = vklad
# nacti()
# print(str(datetime.datetime.now()) + "point> ", ccpoint, " actual> ", ccactual)
# print(sestav_vetu())

while run:
    try:
        nacti()
    except Exception:
        time.sleep(10)
        continue
    sys.stdout.write('.')
    sys.stdout.flush()
    # veta = str(datetime.datetime.now()) + " : " + par + " : act >" + str(ccactual) + "<: "

    if (ccactual - ccpoint) > (ccactual * provize):  # zvyseni stav ovice jak 0,4% - nastav prodej

        if stav=="prodej":  # pridat kontrolu stavu a upravu plusu
            plus += 1
        else:
            stav="prodej"
            plus = 0

        #veta = veta  + stav
        ccpoint = ccactual
        # zapis()
    if (ccpoint - ccactual) > (ccactual * provize):  # snizeni stav o 0,4% - nakup

        if stav=="nakup":
            plus += 1
        else:
            stav="nakup"
            plus = 0
        ccpoint = ccactual

    if plus != 0:
       if plus == 1:
          vloz = 0.38195
       elif plus >=2 and plus <=4:
           vloz = 0.5
       elif plus >= 5 and plus <= 7:
           vloz = 0.7
       elif plus > 8:
           vloz = 0.8

    if stav == "prodej" and ccactual < cclast and (ccactual/ccstart)-1 > rozhodcibod :
        if (stavlast == stav and ccactual > prodejpri) or stavlast != stav:
            actvol()
            print("naposledy nakoupeno za >" + str(nakuppri))
            time.sleep(2)
            if currencyvol > 0.0:
                zapis("uskutecni prodej >")
                print(currency + " >> " + str(currencyvol) + " : " + maincurr + " >> " + str(maincurrvol) + " .")
                print(yobit_api.TradeApi(key=yobit_key, secret_key=yobit_secret_key).sell(par, ccactual, currencyvol * vloz))
                zapis("prodej " + str(ccactual) + " za " + str(currencyvol * vloz))
                sql_obchod(str(currencyvol * vloz))
                prodejpri = ccactual
                ccstart = ccactual

    if stav == "nakup" and ccactual > cclast  and (ccstart/ccactual)-1 > rozhodcibod :
        actvol()
        print("naposledy prodano za >" + str(prodejpri))
        time.sleep(2)
        # for nabidka in aktivni_obchody(pair,"buy"):
         #   print(" nabidka[0]> " + str(nabidka[0]) + " nabidka[1] > " + str(nabidka[1]))
        if (stavlast == stav and ccactual < nakuppri) or stavlast != stav :
            if maincurrvol > 0.0:
            # if prodejpri == 0 or ccactual < prodejpri:
                zapis("uskutecni nakup >")  # , str(aktivni_obchody(pair,"buy")))
                print(currency + " >> " + str(currencyvol) + " : " + maincurr + " >> " + str(maincurrvol) + " .")
                nakup = (maincurrvol * vloz)/ccactual
                print("budem nakupovat za >" + str((maincurrvol * vloz)))
                print(yobit_api.TradeApi(key=yobit_key, secret_key=yobit_secret_key).buy(par, ccactual, nakup))
                zapis("nakup "+str(ccactual)+" za "+str(maincurrvol * vloz))
                sql_obchod(str(maincurrvol * vloz))
                nakuppri = ccactual
                ccstart = ccactual

    if ccactual != cclast:
        print(str(ccactual) + " ccstart/ccactual>" + str(ccstart/ccactual) + " ccactual/ccstart>" + str(ccactual/ccstart) + "point>" + str(ccpoint))
    cclast=ccactual

    time.sleep(10)
# sql_obchod(0.0123)
# prodam print(yobit_api.TradeApi(key=yobit_key, secret_key=yobit_secret_key).buy("eth_usd", 634.365, 0.015))

#print(yobit_api.TradeApi(key=yobit_key, secret_key=yobit_secret_key).get_active_orders("eth_usd"))
#yobit_api.TradeApi(key=yobit_key, secret_key=yobit_secret_key).buy(pair, ccactual, maincurrvol )
# 17.3 12:44 eth >> 0.015 : usd >> 11.52376607
# 13>58  eth >> 0.02003553 : usd >> 6.00754875
    # toto zatim neresit

#    else:
#        vloz=vklad
    # print(veta)
