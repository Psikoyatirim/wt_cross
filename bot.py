import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from tvDatafeed import TvDatafeed, Interval
from ta.trend import EMAIndicator, SMAIndicator
import requests
import time
import os
from datetime import datetime

# =====================
# TELEGRAM AYARLARI
# =====================
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8035211094:AAEqHt4ZosBJsuT1FxdCcTR9p9uJ1O073zY')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1002715468798')

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"}, timeout=15)
        if r.status_code == 200:
            print("📤 Telegram gönderildi", flush=True)
        else:
            print(f"⚠️ Telegram hatası: {r.status_code}", flush=True)
    except Exception as e:
        print(f"⚠️ Telegram bağlantı hatası: {e}", flush=True)

def telegram_parcali(baslik, satirlar, parca_basina=20):
    if not satirlar:
        return
    toplam = (len(satirlar) + parca_basina - 1) // parca_basina
    for i in range(0, len(satirlar), parca_basina):
        parca = satirlar[i:i + parca_basina]
        no = (i // parca_basina) + 1
        ek = f" ({no}/{toplam})" if toplam > 1 else ""
        msg = f"{baslik}{ek}\n\n" + "\n".join(parca)
        telegram_gonder(msg)
        time.sleep(0.5)

# =====================
# SUNUCU AYARLARI (SABİT)
# =====================
INTERVAL = Interval.in_4_hour
INTERVAL_ADI = "4 Saat"
BARS = 500
SCAN_INTERVAL_SECONDS = 1800  # 30 dakika

# =====================
# BIST HİSSELERİ
# =====================
BIST_ALL_SYMBOLS = [
    'A1CAP','ACSEL','ADEL','ADESE','ADGYO','AEFES','AFYON','AGESA','AGHOL','AGROT',
    'AGYO','AHGAZ','AKBNK','AKCNS','AKENR','AKFGY','AKFYE','AKGRT','AKMGY','AKSA',
    'AKSEN','AKSGY','AKSUE','AKYHO','ALARK','ALBRK','ALCAR','ALCTL','ALFAS','ALGYO',
    'ALKA','ALKIM','ALMAD','ANELE','ANGEN','ANHYT','ANSGR','ARCLK','ARDYZ','ARENA',
    'ARSAN','ARZUM','ASELS','ASGYO','ASTOR','ASUZU','ATAGY','ATAKP','ATATP','ATEKS',
    'AVGYO','AVHOL','AVOD','AVTUR','AYDEM','AYEN','AYES','AYGAZ','AZTEK','BAGFS',
    'BAKAB','BALAT','BANVT','BASCM','BAYRK','BEGYO','BERA','BEYAZ','BFREN','BIMAS',
    'BIOEN','BIZIM','BJKAS','BLCYT','BMSTL','BNTAS','BORLS','BOSSA','BRISA','BRKSN',
    'BRSAN','BRYAT','BSOKE','BTCIM','BUCIM','BURCE','BURVA','BVSAN','CANTE','CCOLA',
    'CELHA','CEMAS','CEMTS','CIMSA','CLEBI','CMENT','COSMO','CRDFA','CRFSA','CUSAN',
    'CWENE','DAGI','DARDL','DENGE','DERIM','DESA','DESPC','DEVA','DGGYO','DITAS',
    'DMRGD','DMSAS','DOAS','DOCO','DOFER','DOGUB','DOHOL','DOKTA','DYOBY','DZGYO',
    'EBEBK','ECILC','ECZYT','EDIP','EGEEN','EGEPO','EGGUB','EGSER','EKGYO','EKOS',
    'EKSUN','EMKEL','ENERY','ENJSA','ENKAI','EPLAS','ERBOS','EREGL','ERSU','ESCOM',
    'ESEN','ETILR','EUHOL','EUPWR','EUREN','EYGYO','FENER','FONET','FORMT','FORTE',
    'FRIGO','FROTO','GARAN','GEDIK','GEDZA','GENIL','GENTS','GEREL','GESAN','GIPTA',
    'GLBMD','GLCVY','GLRMK','GLYHO','GMTAS','GOLTS','GOODY','GOZDE','GRSEL','GSDDE',
    'GSDHO','GSRAY','GUBRF','GWIND','HALKB','HATEK','HATSN','HEDEF','HEKTS','HLGYO',
    'HOROZ','HRKET','HUBVC','HUNER','HURGZ','ICBCT','IDGYO','IHLAS','IHLGM','IMASM',
    'INDES','INFO','INTEK','INVEO','INVES','ISCTR','ISDMR','ISFIN','ISGSY','ISKUR',
    'ISMEN','IZENR','IZMDC','JANTS','KAPLM','KAREL','KARSN','KARTN','KATMR','KAYSE',
    'KBORU','KCHOL','KENT','KGYO','KIMMR','KLGYO','KLKIM','KLMSN','KLNMA','KLRHO',
    'KLSER','KLSYN','KMPUR','KNFRT','KONKA','KONTR','KONYA','KOPOL','KORDS','KOTON',
    'KRDMA','KRDMB','KRDMD','KRONT','KRSTL','KRTEK','KRVGD','KSTUR','KTSKR','KUTPO',
    'KUYAS','LIDER','LIDFA','LINK','LOGO','LUKSK','MAALT','MAGEN','MAKIM','MANAS',
    'MARBL','MARKA','MARTI','MAVI','MEDTR','MEGAP','MEGMT','MEPET','MERCN','MERIT',
    'MERKO','METRO','MGROS','MNDRS','MOBTL','MPARK','MRSHL','MSGYO','MTRKS','NATEN',
    'NETAS','NIBAS','NTGAZ','NTHOL','NUGYO','NUHCM','OBASE','ODAS','ORGE','ORMA',
    'OSTIM','OTKAR','OTTO','OYAKC','OYLUM','OZGYO','OZRDN','OZSUB','PAGYO','PARSN',
    'PATEK','PEKGY','PENTA','PETKM','PETUN','PGSUS','PKART','PKENT','PNSUT','POLHO',
    'PRDGS','PRKAB','PRKME','PSGYO','QNBFK','QNBTR','RAYSG','RGYAS','RODRG','RUBNS',
    'RYSAS','SAHOL','SANEL','SANFM','SANKO','SARKY','SASA','SAYAS','SEGMN','SEGYO',
    'SEKUR','SELEC','SELVA','SILVR','SISE','SKBNK','SKTAS','SMART','SNGYO','SNPAM',
    'SOKM','SONME','SUMAS','SUNTK','SUWEN','TATGD','TAVHL','TBORG','TCELL','TDGYO',
    'TEKTU','TGSAS','THYAO','TKFEN','TKNSA','TLMAN','TMSN','TOASO','TRGYO','TRHOL',
    'TRILC','TRMET','TRALT','TSKB','TTKOM','TTRAK','TUKAS','TUPRS','TURSG','ULKER',
    'ULUSE','ULUUN','UNLU','USAK','VAKBN','VAKKO','VANGD','VBTYZ','VERTU','VESBE',
    'VESTL','VKGYO','VKING','VSNMD','YATAS','YAYLA','YBTAS','YESIL','YGGYO','YIGIT',
    'YKBNK','YONGA','YUNSA','YYAPI','ZEDUR','ZOREN','ZRGYO'
]

# =====================
# WAVETREND HESAPLAMA
# =====================
def wavetrend(df, n1=10, n2=21):
    df["HLC3"] = (df["high"] + df["low"] + df["close"]) / 3
    esa = EMAIndicator(df["HLC3"], n1).ema_indicator()
    d = EMAIndicator(abs(df["HLC3"] - esa), n1).ema_indicator()
    ci = (df["HLC3"] - esa) / (0.015 * d)
    tci = EMAIndicator(ci, n2).ema_indicator()
    df["wt1"] = tci
    df["wt2"] = SMAIndicator(tci, 4).sma_indicator()
    return df

# =====================
# TARAMA
# =====================
def tarama_yap(tv, scan_number=1):
    signals = []
    toplam = len(BIST_ALL_SYMBOLS)

    print(f"\n{'='*50}", flush=True)
    print(f"🔍 TARAMA #{scan_number} — {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", flush=True)
    print(f"{'='*50}", flush=True)

    for i, symbol in enumerate(BIST_ALL_SYMBOLS, 1):
        if i % 50 == 1:
            print(f"📈 [{i}/{toplam}] İşleniyor...", flush=True)
        try:
            df = tv.get_hist(symbol=symbol, exchange="BIST", interval=INTERVAL, n_bars=BARS)
            if df is None or len(df) < 50:
                continue

            df = wavetrend(df)
            last = df.iloc[-1]
            prev = df.iloc[-2]

            if (prev["wt1"] < prev["wt2"]) and (last["wt1"] > last["wt2"]):
                signals.append({
                    "sembol": symbol,
                    "fiyat": round(float(last["close"]), 2),
                    "wt1": round(float(last["wt1"]), 2),
                    "wt2": round(float(last["wt2"]), 2),
                })
                print(f"  🚨 SİNYAL: {symbol} — {round(float(last['close']), 2)} TL", flush=True)

        except Exception:
            continue

        time.sleep(0.3)

    print(f"✅ Tamamlandı! {len(signals)} sinyal bulundu.", flush=True)
    return signals


# =====================
# ANA DÖNGÜ
# =====================
if __name__ == "__main__":
    print("🚀 WaveTrend Cross Otomatik Tarayıcı Başladı", flush=True)
    print(f"📈 Interval: {INTERVAL_ADI} | Her 30 dakikada bir", flush=True)

    tv = TvDatafeed()

    telegram_gonder(
        f"🤖 <b>WaveTrend Cross Bot Aktif</b>\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
        f"⏰ Interval: {INTERVAL_ADI}\n"
        f"🔄 Her 30 dakikada bir tarama yapılacak\n"
        f"📊 {len(BIST_ALL_SYMBOLS)} hisse takip ediliyor"
    )

    scan_count = 0
    while True:
        scan_count += 1
        simdi = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

        try:
            signals = tarama_yap(tv, scan_number=scan_count)

            if signals:
                telegram_gonder(
                    f"🚨 <b>WaveTrend Cross — #{scan_count}</b>\n"
                    f"📅 {simdi}\n"
                    f"⏰ {INTERVAL_ADI}\n\n"
                    f"✅ AL Sinyali: {len(signals)} hisse"
                )
                time.sleep(0.5)

                satirlar = [
                    f"<b>{s['sembol']}</b> — {s['fiyat']} TL  |  WT1: {s['wt1']}  WT2: {s['wt2']}"
                    for s in signals
                ]
                telegram_parcali("📈 <b>AL SİNYALLERİ</b>", satirlar)

            else:
                telegram_gonder(
                    f"📊 <b>WaveTrend Cross — #{scan_count}</b>\n"
                    f"📅 {simdi}\n"
                    f"⏰ {INTERVAL_ADI}\n\n"
                    f"❌ AL sinyali bulunamadı\n"
                    f"⏳ Sonraki tarama 30 dakika sonra..."
                )

        except Exception as e:
            print(f"❌ Tarama hatası: {e}", flush=True)
            telegram_gonder(f"⚠️ Tarama hatası: {str(e)[:100]}\n🔄 30 saniye sonra yeniden deneniyor...")
            time.sleep(30)
            continue

        print(f"\n⏳ 30 dakika bekleniyor...", flush=True)
        time.sleep(SCAN_INTERVAL_SECONDS)
