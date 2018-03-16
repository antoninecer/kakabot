import yobit_api, json, time, requests, datetime, sys

maincurr = 'usd' #usd
currency = 'doge' #doge
par = currency + '_' + maincurr
interest = ('doge', 'usd')
yobit_key = 'key'
yobit_secret_key = 'secret'
run = True
vklad=0.2 # kolik dat na jeden obchod z celkoveho mnozstvi
provize=0.004 # obvykle yobit ma 2%, coz je 0.002 , ja tu mam 0.004, kde tedy chci mit i ja 0.2% :)

#promenne pro muj algoritmus
stav = 'nic'
ccactual = 0.00
cclast = 0.00
ccpoint = 0.00
plus = 0  #tady bych mel zvysovat hodnoty kdyz se opakuje prodej prodej, nebo nakup nakup po sobe pro vice nakupu/prodeje
nakuppri=0.00 #abych neprodal levn2ji, nez nakoupil
prodejpri=0.00 #abych nekoupil draz, nez prodal
maincurrvol = 0.00 # nacte z penezenky
currencyvol = 0.00 # nacte z penezenky





# sem dat z nactenihtml.py a udelat funkci na nejlepsi prodej/nakup
def aktivni_obchody(menovypar,co): #doge_usd, buy/sell
    # https://yobit.net/api/3/depth/btc_usd?limit=5
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
        if True: #(currency in interest)
            if (currency != maincurr):
                hodnota = yobit_api.PublicApi().get_pair_ticker(par)
                print(currency.upper(), count, "prumer >" + str(hodnota.get('avg')) + " aktualne >" + str(hodnota.get('last')) + " nakup >" + str(hodnota.get('buy')) + " prodej >" + str(hodnota.get('sell')))

def actvol(): #naplni  maincurrvol a currencyvol stavem z penezenky
    global maincurrvol, currencyvol
    for mena, count in wallet.items():
        if (mena == maincurr):
            maincurrvol = count
        if (mena == currency):
            currencyvol = count


def nacti():
    global ccpoint, ccactual
    usd = 0
    doge = 0
    #print(pair)
    hodnota = yobit_api.PublicApi().get_pair_ticker(pair=par)
    #print(pair.upper(), "prumer >" + str(hodnota.get('avg')) + " aktualne >" + str(hodnota.get('last')) + " nakup >" + str(hodnota.get('buy')) + " prodej >" + str(hodnota.get('sell')))
    ccactual = hodnota.get('last')
    if (ccpoint == 0):
        ccpoint = ccactual
    link = "https://yobit.net/api/3/depth/" + par + "?limit=10"
    f = requests.get(link)
    #print("prvních 10")
    # print (f.json().get(pair))
    nabidky = f.json().get(par).get('asks')
    poptavky = f.json().get(par).get('bids')
    #print("Nabidky - ostatni prodavaji")
    for nabidka in nabidky:
        usd += nabidka[0] * nabidka[1]
    #    print(nabidka[0], " kusu> ", nabidka[1], "za ", nabidka[0] * nabidka[1], "USD", )
    #print("Celkem za ", usd)

    #print("Poptávky - ostatni nakupuji")
    for poptavka in poptavky:
        usd += poptavka[0] * poptavka[1]
    #    print(poptavka[0], " kusu> ", poptavka[1], "za ", poptavka[0] * poptavka[1], "USD", )
    #print("Celkem za ", usd)


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

def sestav_vetu():
    global ccpoint, ccactual, cclast, stav, plus
    text = str(datetime.datetime.now()) + " : " + par + " Point: " + str(ccpoint) + " last: " + str(cclast) + " actual: " + str(ccactual) + " Stav >" + stav + "< plus:>" + str(plus) + "<\n"
    return text


#zacatek programu - nacteme udaje z penezenky
dotaz = yobit_api.TradeApi(key=yobit_key, secret_key=yobit_secret_key).get_info() #penezenky a stavy v json
account = dotaz.get('return')
wallet = account.get('funds')

actvol()
print (currency + " >> " + str(currencyvol) + " : " + maincurr + " >> " + str(maincurrvol) + " .")

nacti()
#print(str(datetime.datetime.now()) + "point> ", ccpoint, " actual> ", ccactual)
print(sestav_vetu())
while run:
    nacti()
    sys.stdout.write('.')
    veta = str(datetime.datetime.now()) + " : " + par + " : act >" + str(ccactual) + "<: "

    #print(veta)
    if (ccactual - ccpoint) > (ccactual * provize): #zvyseni stav o 0,4% - prodej

        if stav=="prodej": # pridat kontrolu stavu a upravu plusu
            plus += 1
        else:
            stav="prodej"
            plus = 0

        veta = veta  + stav
        ccpoint = ccactual
        zapis()
    if (ccpoint - ccactual) > (ccactual * provize): #snizeni stav o 0,4% - nakup

        if stav=="nakup":
            plus += 1
        else:
            stav="nakup"
            plus = 0

        veta = veta + stav
        ccpoint = ccactual
        zapis()
    if stav == "prodej" and ccactual < cclast :

        penezenka()
        actvol()

        #for poptavka in aktivni_obchody(pair,"sell"):
         #   print("poptavka[0]> " + str(poptavka[0]) + " poptavka[1]> " + str(poptavka[1]))

        if currencyvol > 0.0:
            zapis("uskutecni prodej >")
            print(currency + " >> " + str(currencyvol) + " : " + maincurr + " >> " + str(maincurrvol) + " .")
            yobit_api.TradeApi(key=yobit_key, secret_key=yobit_secret_key).sell(par, ccactual, currencyvol * vklad)
            zapis("prodej " + str(ccactual) + " za " + str(currencyvol * vklad))
            prodejpri = ccactual

    if stav == "nakup" and ccactual > cclast :

        penezenka()
        actvol()

        #for nabidka in aktivni_obchody(pair,"buy"):
         #   print(" nabidka[0]> " + str(nabidka[0]) + " nabidka[1] > " + str(nabidka[1]))
        if maincurrvol > 0.0:
            zapis("uskutecni nakup >")  # , str(aktivni_obchody(pair,"buy")))
            print(currency + " >> " + str(currencyvol) + " : " + maincurr + " >> " + str(maincurrvol) + " .")
            yobit_api.TradeApi(key=yobit_key, secret_key=yobit_secret_key).buy(par, ccactual, maincurrvol * vklad)
            zapis("nakup "+str(ccactual)+" za "+str(maincurrvol * vklad))
            nakuppri = ccactual

    if ccactual != cclast:
        print(ccactual)
    cclast=ccactual

    time.sleep(10)

#yobit_api.TradeApi(key=yobit_key, secret_key=yobit_secret_key).buy(pair, ccactual, maincurrvol )