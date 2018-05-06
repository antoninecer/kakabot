import yobit_api, json, time, requests, datetime, mysql.connector,socket, sys, smtplib

# pair
maincurr = 'usd'  # usd-btc-doge-rur-eth-waves
currency = 'doge'  # doge, eth
# yobit api
yobit_key = 'key'
yobit_secret_key = 'secret'
# access to databaze
db = "kakabot"
uzivatel = "root"
heslo = "password"
server = "127.0.0.1"
# napojeni mailu
fromaddr = 'rkakabot@gmail.com'
toaddrs = 'antoninecer@gmail.com'
musername = 'rkakabot@gmail.com'
mpassword = 'password'
import yobit_api, json, time, requests, datetime, mysql.connector,socket, sys, smtplib

# promenne pro muj algoritmus
delay = 60  # spozdeni v sekundach
rozhodcibod = 0.007 # 0.01 je 1 procento - kdy uskutecnit obchod kdyz se kurz zmeni o toto
nakuppri=0 # abych neprodal levneji, nez nakoupil
prodejpri=0  # abych nekoupil draz, nez prodal
vklad = 0.2  # kolik dat na jeden obchod z celkoveho mnozstvi
provize = 0.003618  # obvykle yobit ma 0,2%, coz je 0.002 , ja tu mam 0.004, kde tedy chci mit i ja 0.2% :)
maxvkladcurr = 0  # maximalni vklad na jeden prodej currency
maxvkladmaincurr = 100  # maximalni vklad pro nakup currebncy v maincurr
minvkladcurr=0
nosecuremod = False  # True  # tady neberu v pota nakupy a prodeje pokud je True
looktooffers = True  # jestli se koukat do nabidek a nejet jen na spicky
fullhouse = False  # jestli ma obchodovat se vsim co ma do vyse

minvkladmaincurr=0.1  # minimalni vklad 0.1 USD
obchodza = 0  # za kolik bude uskutecnen obchod
stav = 'nic'
stavlast = 'nic'
ccactual = 0.00
cclast = 0.00
ccpoint = 0.00
ccstart = 0.0
plus = 0  # zvysovat hodnoty kdyz se opakuje prodej prodej, nebo nakup nakup po sobe pro vice nakupu/prodeje
maincurrvol = 0.00  # nacte z penezenky
currencyvol = 0.00  # nacte z penezenky
par = currency + '_' + maincurr
ostatniprodej = 0
ostatninakup = 0
dot = 0  # tecka
dnesniprumerkurznakup = 0
dnesniprumerkurzprodej = 0
dnesnakoupenocc = 0
dnesprodanocc = 0
dnesnakoupenomaincurr = 0
dnesprodanomaincurr = 0
maximalnipocetcurr = 200000  # pokud dosahneme maximalni pocet, bude dobre prodat a nakoupit jinou menu, treba btc
pomerprevodudozalohy = 0.2
zaloznicurr = 'btc'  # kam odlevat prebytecne currency
reset = "yes"  # priznak jestli po nakupu vyresetovat ccpoint a ccstart na ccactual (kdyz vybiram z nabidek, tak nemohu resetovat reset = "noreset")

run = True  # jestli se spusti program hodnota True / False

def sendmail(subject, msg):
    global fromaddr, toaddrs, musername, mpassword
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        message = 'Subject: {}\n\n{}'.format(subject, msg)
        server.login(musername, mpassword)

        server.sendmail(fromaddr, toaddrs, msg)
        server.quit()
        # ...send emails
    except:
        print('Something went wrong...')


def aktivni_obchody(menovypar,co):  # vybere 3 nejlepsi nabizene obchody na yobitu :menovypar "ltc_usd" :co sell/buy
    mam = False
    navrat = 0
    while not mam:
        try:
            link = "https://yobit.net/api/3/depth/" + menovypar + "?limit=3"
            f = requests.get(link)
            nabidky = f.json().get(par).get('bids')
            poptavky = f.json().get(par).get('asks')
            if co == "buy" or co == "nakup":
                navrat = nabidky
            if co == "sell" or co == "prodej":
                navrat = poptavky
            mam = True
        except:
            print("nepovedlo se načíst údaje o aktivních obchodech, zkusím to znovu za pár vteřin")
            time.sleep(2)
    return navrat

def actvol(*s):  # naplni  maincurrvol a currencyvol stavem z penezenky pokud s=="all" vypise vse v penezence
    global maincurrvol, currencyvol, maincurr, currency
    try:
        dotaz = yobit_api.TradeApi(key=yobit_key, secret_key=yobit_secret_key).get_info()  # penezenky a stavy v json
        account = dotaz.get('return')
        wallet = account.get('funds')
        for mena, count in wallet.items():
            if (mena == maincurr):
                maincurrvol = count
            if (mena == currency):
                currencyvol = count
        print(currency + " >> " + str(currencyvol) + " : " + maincurr + " >> " + str(maincurrvol) + " .")
        for i in s:
            if s == "all":
                for currency, count in wallet.items():
                    hodnota = yobit_api.PublicApi().get_pair_ticker(par)
                    print(currency.upper(), count, "prumer >" + str(hodnota.get('avg')) + " aktualne >" + str(
                    hodnota.get('last')) + " nakup >" + str(hodnota.get('buy')) + " prodej >" + str(
                    hodnota.get('sell')))
    except:
        print('Nastala neočekávaná chyba v actvol')

def nacti():  # nacte hodnotu cc
    global ccpoint, ccactual, ccstart, maxvkladcurr
    try:
        hodnota = yobit_api.PublicApi().get_pair_ticker(pair=par)
        ccactual = hodnota.get('last')
        if ccactual is None:
            ccactual = cclast
        maxvkladcurr = maxvkladmaincurr / ccactual
        # {'high': 603.3402, 'low': 481.50898705,
        # 'avg': 542.42459352, 'vol': 566012.01104146, 'vol_cur': 1082.91016055,
        # 'last': 532.42971141, 'buy': 530.92620723, 'sell': 532.42971141, 'updated': 1521406380}
        if (ccpoint == 0):  # prvotni nastaveni ccpoint
            ccpoint = ccactual
            ccstart = ccactual
    except:
        print('Nastala neocekavana chyba v nacti')

def zapis(*s):
    global ccpoint,stav,plus,vloz,vklad
    file = open("log_" + par + ".txt", "a")
    for i in s:
        print(i)
        file.write(i)
    print(sestav_vetu())
    file.write(sestav_vetu())
    file.close()
    ccpoint = ccactual


def sql_obchod(kolik, poznamka, id):
    global ccactual, stav, maincurr, currency, plus
    cnx = mysql.connector.connect(user=uzivatel, password=heslo, host=server, database=db)
    x = cnx.cursor()
    veta = "insert into kakabot.kakabot(cas, maincurr, currency, stav, kurz, kolik, kdo, plus, popis, yoid) values('"
    veta += str(datetime.datetime.now()) + "', '" + maincurr + "', '" + currency + "', '" + stav + "',"
    veta += str(ccactual) + "," + str(kolik) + ",'" + socket.gethostname()  + "'," + str(plus) +", '" + str(poznamka) + "','" + str(id) + "');"
    print(veta)
    try:
        print(x.execute(veta))
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

def sql_suma_dnes():  # vrati kolik dnes bylo za stav obchodovano
    global ccactual, currency, maincurr,dnesniprumerkurzprodej,dnesprodanocc,dnesprodanomaincurr,dnesniprumerkurznakup,dnesnakoupenocc,dnesnakoupenomaincurr
    try:
        cnx = mysql.connector.connect(user=uzivatel, password=heslo, host=server, database=db)
        x = cnx.cursor()
        stav = "prodej"
        veta = "select stav,sum(za)/sum(kolik) as kurz, sum(kolik) as cc, sum(za) as za from (select stav,kolik, kurz * kolik as za from kakabot.kakabot where maincurr = '" + maincurr + "' and currency = '" + currency + "' and date(cas) = CURDATE()) as a where a.stav ='" + stav + "' group by stav;"
        # print(veta)
        x.execute(veta)
        vysledek = x.fetchall()
        for x in vysledek:
            dnesniprumerkurzprodej = x[1]
            dnesprodanocc = x[2]
            dnesprodanomaincurr = x[3]
        cnx.close()
        # tady jsem musel ukoncit a znovu zacis sql, jinak mi to furt vyhazovalo chybu
        time.sleep(1)
        cnx = mysql.connector.connect(user=uzivatel, password=heslo, host=server, database=db)
        x = cnx.cursor()
        stav = "nakup"
        veta = "select stav,sum(za)/sum(kolik) as kurz, sum(kolik) as cc, sum(za) as za from (select stav,kolik, kurz * kolik as za from kakabot.kakabot where maincurr = '" + maincurr + "' and currency = '" + currency + "' and date(cas) = CURDATE()) as a where a.stav ='" + stav + "' group by stav;"
        # print(veta)
        x.execute(veta)
        vysledek = x.fetchall()
        for x in vysledek:
            dnesniprumerkurznakup = x[1]
            dnesnakoupenocc = x[2]
            dnesnakoupenomaincurr = x[3]
    except:
        print("nepovedlo se")


def sestav_vetu():
    global ccpoint, ccactual, cclast, stav, plus
    text = str(datetime.datetime.now()) + " : " + par + " Point: " + str(ccpoint) + " last: " + str(cclast) + " actual: " + str(ccactual) + " Stav >" + stav + "< plus:>" + str(plus) + "<\n"
    return text

def nakupzaloha(kolik):  # pokud dosahneme ur4iteho mnozstvi treba 600000 doge, pak za p5ebytek nakup treba btc a zde je za kolik doge koupim btc (prodam doge)
    global zaloznicurr,currencyvol, currency, maximalnipocetcurr
    zakolik = currencyvol - maximalnipocetcurr
    print(str(datetime.datetime.now()) +" budem nakupovat : " + zaloznicurr + " za >" + str(zakolik) + " " + currency)
    zaloznipar = currency + '_' + zaloznicurr
    hodnota = yobit_api.PublicApi().get_pair_ticker(pair=zaloznipar)
    kurz = hodnota.get('last')
    time.sleep(1)
    #  musim dodelat, ted nemohu, vraci se milacek
    odpoved = yobit_api.TradeApi(key=yobit_key, secret_key=yobit_secret_key).sell(zaloznipar, kurz, kolik)
    print(odpoved)
    o = json.loads(json.dumps(odpoved))
    print(o["success"])
    if o["success"] == 1:  #podařilo se zadat nabídku na prodej do yobit
        re = json.loads(json.dumps(o["return"]))
        #    print(re["order_id"])
        #   print(re["server_time"])
        zapis("nakup " + str(kurz) + " za " + str(zakolik) + " " + maincurr)


def nakupyo(kurz,zakolik,poznamka):
    global nakuppri, cclast, ccstart, ccpoint, currencyvol, maincurrvol
    nakup = zakolik  / kurz
    print(str(datetime.datetime.now()) +" budem nakupovat : " + currency + " za >" + str(zakolik) + " " + maincurr)
    print(nakup)
    if dnesniprumerkurzprodej > kurz or nosecuremod:  # if prodejpri > kurz or nosecuremod:
        odpoved = yobit_api.TradeApi(key=yobit_key, secret_key=yobit_secret_key).buy(par, kurz, nakup)
        print(odpoved)
        o = json.loads(json.dumps(odpoved))
        print(o["success"])
        if o["success"] == 1:  #podařilo se zadat nabídku na prodej do yobit
            re = json.loads(json.dumps(o["return"]))
        #    print(re["order_id"])
        #   print(re["server_time"])
            zapis("nakup " + str(kurz) + " za " + str(zakolik) + " " + maincurr)
            sql_obchod(str(nakup), str(poznamka), re["order_id"])
            fu = json.loads(json.dumps(re["funds"]))  # aktualizuji currencyvol a maincurrvol
            maincurrvol = fu[maincurr]
            currencyvol = fu[currency]
            nakuppri = kurz
            if reset == "noreset":
                print("neresetuji promenne ccpoint a ccstart")
            else:
                ccpoint = kurz
                ccstart = kurz
                stav = "nic"
                plus = 0
                vloz = vklad
    else:
        odpoved = "toto neprovedu, jelikoz prumerny nakup byl za " + str(dnesniprumerkurzprodej) + " a ted chci nakupovat za " + str(kurz)
        print(odpoved)

def prodejyo(kurz,zakolik,poznamka):  # prodej na yobit.net parametry kurz, za kolik v maincurr, poznamka
    global prodejpri, cclast, ccstart, ccpoint, currencyvol, maincurrvol
    print(str(datetime.datetime.now()) +" budem prodavat :  >" + str(zakolik) + " " + currency)
    if dnesniprumerkurznakup < kurz or nosecuremod:  # if nakuppri < kurz or nosecuremod:
        odpoved = yobit_api.TradeApi(key=yobit_key, secret_key=yobit_secret_key).sell(par, kurz, zakolik)
        print(odpoved)
        o = json.loads(json.dumps(odpoved))
        print(o["success"])
        if o["success"] == 1:  #podařilo se zadat nabídku na prodej do yobit
            re = json.loads(json.dumps(o["return"]))
            # print(re["order_id"])
            # print(re["server_time"])
            zapis("prodej v kurzu" + str(kurz) + " za " + str(zakolik) + " " + currency)
            sql_obchod(str(zakolik), str(poznamka), re["order_id"])
            fu = json.loads(json.dumps(re["funds"]))  # aktualizuji currencyvol a maincurrvol
            maincurrvol = fu[maincurr]
            currencyvol = fu[currency]
            prodejpri = kurz
            if reset == "noreset":
                print("neresetuji promenne ccpoint a ccstart")
            else:
                ccpoint = kurz
                ccstart = kurz
                stav = "nic"
                plus = 0
                vloz = vklad
    else:
        odpoved = "toto neprovedu, jelikoz prumerny prodej byl za " + str(dnesniprumerkurznakup) + " a ted chci nakupovat za " + str(kurz)
        print(odpoved)


def aktivni_objednavky():
    s = yobit_api.TradeApi(yobit_key, yobit_secret_key).get_active_orders(par)
    print(s)
    o = json.loads(json.dumps(s))
    if o["success"] == 1:
        print(o["success"])
        re = json.loads(json.dumps(o["return"]))
        for i in re:
            yobitid = i  # kouknu do kakabot tabulky kde yoid - yobitid
            rf = json.loads(json.dumps(re[i]))
            print(rf)
            print(rf["type"])
            print(rf["amount"])
            print(rf["rate"])

def tecka():
    global dot
    if dot >= 18:  # po 3 minutach udelej dalsi radek
        print("po 18 teckach " +str(datetime.datetime.now()) + " : " + par + " : act >" + str(ccactual) + "<:")
        dot = 0
    dot += 1
    sys.stdout.write('.')
    sys.stdout.flush()

def vynuluj_promenne():
    dnesniprumerkurznakup = 0
    dnesniprumerkurzprodej = 0
    ccstart = ccpoint
    plus = 0


# zacatek programu - nacteme udaje z penezenky a kouknem za kolik jsme naposled nakoupili a prodali
actvol()
if nakuppri == 0:
    nakuppri=sql_posledni("nakup")
if prodejpri == 0:
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
print("< rozhodcibod >" + str(rozhodcibod))
while run:
    if datetime.datetime.now().hour == 0 and datetime.datetime.now().minute <= 5:  # prvnich 5 minut po pulnoci nebudu obchodovat
        vynuluj_promenne()
        print("je po pulnoci a nuluji promenne")
        time.sleep(delay)
        continue

    if currencyvol > maximalnipocetcurr:
        prevod = maximalnipocetcurr * pomerprevodudozalohy
        nakupzaloha(prevod)

    try:
        nacti()
    except Exception:
        time.sleep(10)
        continue
    sql_suma_dnes() #nacte z sql kolik se toho dnes prumerne prodalo a koupilo promenne: dnesniprumerkurzprodej,dnesprodanocc,dnesprodanomaincurr,dnesniprumerkurznakup,dnesnakoupenocc,dnesnakoupenomaincurr
    if dnesniprumerkurzprodej == 0:
        dnesniprumerkurzprodej = ccactual
    if dnesniprumerkurznakup == 0:
        dnesniprumerkurznakup = ccactual
    #  print("dnesniprumerkurznakup: " + str(dnesniprumerkurznakup) + " dnesniprumerkurzprodej: "+ str(dnesniprumerkurzprodej))

    if reset == "noreset":  # do3lo k nakupu / prodeji z nabidek bylo plus
        stav = "nic"
        plus = 0
        reset = "yes"

    tecka()

    if abs(ccstart - ccactual) > ((ccactual/100)*2):
        sendmail('prekroceny 2%','start: '+str(ccstart)+' aktualni: '+str(ccactual))

    if (ccactual - ccpoint)  >= (ccactual * provize):  # zvyseni stav ovice jak 0,4% - nastav prodej
        if stav=="prodej":  # pridat kontrolu stavu a upravu plusu
            plus += 1
        else:
            stav="prodej"
            plus = 0
        ccpoint = ccactual
        # zapis()

    if (ccpoint - ccactual) >= (ccactual * provize):  # snizeni stav o 0,4% - nakup
        if stav=="nakup":
            plus += 1
        else:
            stav="nakup"
            plus = 0
        ccpoint = ccactual

    if ((ccactual - ccstart) > 0 and (ccactual - ccstart) < (ccactual * provize)) or ((ccstart - ccactual) > 0 and (ccstart - ccactual) < (ccactual * provize)):  # zvyseni stav ovice jak 0,4% - nastav prodej
        stav = "nic"
        plus = 0

    if plus != 0 and not fullhouse:
        if plus == 1:
            vloz = vklad * 1.5  # pri vklad = 0.2 je to 0.3
        elif plus == 2:
          vloz = vklad * 2  # pri vklad = 0.2 je to 0.4
        elif plus >=3:
           vloz = vklad * 2.5  # pri vklad = 0.2 je to 0.5

    if fullhouse:  #budeme obchodovat se všímm do výše maxvkladcurr
        vloz = 1

    if stav == "prodej" and ccactual < cclast and (ccactual/ccstart)-1 > rozhodcibod :
        print("naposledy nakoupeno za >" + str(nakuppri) + " stavlast > " + stavlast + " aktualni kurz > " + str(ccactual))
        if ccactual > nakuppri:
            actvol()
            time.sleep(1)
            if currencyvol > 0.0:
                if currencyvol * vloz > maxvkladcurr:
                    obchodza = maxvkladcurr
                else:
                    obchodza = currencyvol * vloz
                print(currency + " >> " + str(currencyvol) + " : " + maincurr + " >> " + str(maincurrvol) + " .")
                prodejyo(ccactual,obchodza,"prodej pri zmene kurzu")

    if stav == "nakup" and ccactual > cclast  and (ccstart/ccactual)-1 > rozhodcibod :
        actvol()
        print("naposledy prodano za > " + str(prodejpri) + " stavlast > " + stavlast + " aktualni kurz > " + str(ccactual))
        time.sleep(1)
        if (stavlast == stav and ccactual < prodejpri):
            if maincurrvol * vloz > maxvkladmaincurr:
                obchodza = maxvkladmaincurr
            else:
                obchodza = maincurrvol * vloz
            print(currency + " >> " + str(currencyvol) + " : " + maincurr + " >> " + str(maincurrvol) + " .")
            nakupyo(ccactual,obchodza,"nakup pri zmene kurzu")

    if ccactual != cclast:
        rozdil = round(ccactual - cclast,5)
        up = (ccstart / ccactual)  # puvodne bylo ccpoint a ne ccstart
        print(str(datetime.datetime.now().hour) + ":" + str(datetime.datetime.now().minute)+ " Actual >" + str(ccactual) + " rozdil: " + str(rozdil) + " od start " + str(up) + "< last >" + str(cclast) + "< point >" + str(ccpoint) + "< start >" + str(ccstart) + "< plus > " + str(plus) + " < stav > " + stav)

    if plus >= 1 and looktooffers:  # mame zde plus nic aktivne neobchuduji, kouknemese na poptavky a nabidky do yobitu
        if stav == "prodej":
            time.sleep(1)
            print(" kurz je vyssi a koukam se do nabidek jestli tu nenajdu nejakou kde by se dalo s vyhodou prodat ")
            for nakup in aktivni_obchody(par,"buy"):
                print(nakup[0], nakup[1])
                if nakup[0] - ccstart  > ccactual * provize :
                    if nakup[1] <= currencyvol * vloz:  # prodava za mene, nez ja mohu nakupvat
                        obchodza = nakup[1]
                    elif nakup[1] >= currencyvol * vloz:  # Prodava za vice, nez ja mohu nakupovat
                        obchodza = currencyvol * vloz
                    if obchodza > maxvkladcurr:
                        obchodza = maxvkladcurr
                    reset = "noreset"
                    if obchodza > minvkladmaincurr:
                        prodejyo(nakup[0],obchodza,"prodej z nabidky")
                    else:
                        print('nedosazeno minimalniho mnozstvi k prodeji')

        if stav == "nakup":
            time.sleep(1)
            print(" kurz je nizsi a koukam se do nabidek jestli tu nenajdu nejakou kde by se dalo s vyhodou nakoupit ")
            for prodej in aktivni_obchody(par, "sell"):
                print(prodej[0], prodej[1])
                if  ccstart - prodej[0] > ccactual * provize:
                    nakup = (maincurrvol * vloz)/prodej[0]  # dostavame nakup v crypto
                    if prodej[1] <= nakup:  # nakupuje za mene, nez ja mohu prodat
                        obchodza = prodej[1]
                    elif prodej[1] >= nakup:  # nakupuje za vice, nez ja mohu prodat
                        obchodza = nakup
                    if obchodza > maxvkladcurr:
                        obchodza = maxvkladcurr
                    print(currency + " >> " + str(currencyvol) + " : " + maincurr + " >> " + str(maincurrvol) + " .")
                    reset = "noreset"
                    if obchodza*prodej[0] > minvkladmaincurr:
                        nakupyo(prodej[0],obchodza*prodej[0],"nakup z nabidky")
                    else:
                        print('není za co nakupovat')

    cclast=ccactual  # nastavi predchozi kurz aktualnim
    time.sleep(delay)  # pocka nastavenou dobu

# konec programu, dalsi kod se nevykona, pouze pro testovani

# doge >> 11590.50248718 : usd >> 32.90711086 . 27.3.2018 19:30

# nakupzaloha(300)
