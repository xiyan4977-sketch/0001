import requests
import time
import datetime
import re
from bs4 import BeautifulSoup

class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send_alert(self, message):
        payload = {'chat_id': self.chat_id, 'text': message, 'parse_mode': 'Markdown'}
        try:
            requests.post(self.base_url, data=payload)
        except Exception as e:
            print(f"網路錯誤: {e}")

class LimitUpSniper:
    def __init__(self, notifier):
        self.notifier = notifier
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        
        self.watchlist = [] # 清單由爬蟲自動填入
        self.market_type_cache = {} # 自動記憶上市或上櫃，加快後續查詢速度
        self.triggered_stage1 = set()
        self.triggered_stage2 = set()
        
    def fetch_hot_stocks(self):
        """自動爬取 Yahoo 股市『成交值排行榜』前 50 名作為今日飆股名單"""
        print("🕸️ 開始爬取今日熱門飆股...")
        try:
            url = "https://tw.stock.yahoo.com/rank/turnover"
            res = self.session.get(url, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 尋找所有股票代號的連結 (例如 /quote/2330)
            links = soup.find_all('a', href=re.compile(r'/quote/\d{4,5}$'))
            
            hot_stocks = []
            for link in links:
                stock_id = link['href'].split('/')[-1]
                stock_name = link.text.strip()
                if stock_id not in [s['stock_id'] for s in hot_stocks]: # 避免重複
                    hot_stocks.append({'stock_id': stock_id, 'name': stock_name})
                    if len(hot_stocks) >= 50: # 只抓前 50 檔資金最集中的
                        break
            
            self.watchlist = hot_stocks
            stock_names_str = ", ".join([s['name'] for s in hot_stocks[:10]]) + "..."
            self.notifier.send_alert(f"🤖 *爬蟲完畢*：已自動鎖定今日 {len(self.watchlist)} 檔熱門飆股。\n前十名：{stock_names_str}")
            print(f"✅ 成功抓取 {len(self.watchlist)} 檔股票。")
        except Exception as e:
            print(f"❌ 爬蟲失敗: {e}")
            self.notifier.send_alert("⚠️ 抓取熱門飆股失敗，請檢查程式或網路。")

    def get_realtime_price(self, stock_id):
        """取得即時報價，並自動判斷/記憶上市(tse)或上櫃(otc)"""
        # 如果已經知道市場類型，就直接用
        types_to_try = [self.market_type_cache.get(stock_id)] if stock_id in self.market_type_cache else ['tse', 'otc']

        for market_type in types_to_try:
            if not market_type: continue
            url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={market_type}_{stock_id}.tw&json=1&delay=0"
            try:
                res = self.session.get(url + f"&_={int(time.time() * 1000)}", timeout=3)
                data = res.json()
                if data.get('msgArray'):
                    info = data['msgArray'][0]
                    # 記住它是上市還是上櫃，下次就不用猜了
                    self.market_type_cache[stock_id] = market_type 
                    return {
                        'current_price': float(info['z']) if info['z'] != '-' else None,
                        'yesterday_close': float(info['y'])
                    }
            except Exception:
                pass
        return None

    def calculate_limit_up(self, y_close):
        return round(y_close * 1.10, 2)

    def check_and_alert(self):
        for stock in self.watchlist:
            stock_id = stock['stock_id']
            stock_name = stock['name']

            if stock_id in self.triggered_stage2:
                continue

            price_info = self.get_realtime_price(stock_id)
            time.sleep(0.3) # 降低延遲，讓掃描更快

            if not price_info or price_info['current_price'] is None:
                continue

            current = price_info['current_price']
            y_close = price_info['yesterday_close']
            
            if y_close is None or y_close == 0:
                continue

            pct_change = ((current - y_close) / y_close) * 100
            limit_up_price = self.calculate_limit_up(y_close)

            # 🚀 階段二：漲幅突破 7.5% -> 準備鎖漲停！
            if pct_change >= 7.5 and stock_id not in self.triggered_stage2:
                msg = (
                    f"🚀🚀 *【漲停狙擊：馬上買進】* 🚀🚀\n"
                    f"標的：*{stock_name} ({stock_id})*\n"
                    f"現價：{current:.2f} (爆噴 +{pct_change:.2f}%)\n"
                    f"🎯 漲停價：{limit_up_price:.2f}\n"
                    f"⚡ *動作：打開大富翁【市價重壓】，明天開盤隔日沖倒貨！*"
                )
                self.notifier.send_alert(msg)
                self.triggered_stage2.add(stock_id)
                self.triggered_stage1.add(stock_id)

            # 🔥 階段一：漲幅突破 4% -> 列入觀察
            elif pct_change >= 4.0 and stock_id not in self.triggered_stage1:
                msg = (
                    f"🔥 *【動能發動：主力點火】* 🔥\n"
                    f"標的：{stock_name} ({stock_id})\n"
                    f"現價：{current:.2f} (上漲 +{pct_change:.2f}%)\n"
                    f"👀 *備註：突破 7% 時請準備重壓。*"
                )
                self.notifier.send_alert(msg)
                self.triggered_stage1.add(stock_id)

    def run_daily_monitor(self, interval_seconds=15):
        # 1. 程式啟動時，先去抓今天最熱門的股票
        self.fetch_hot_stocks()
        
        self.notifier.send_alert("🔔 *大富翁雷達已啟動*\n開始鎖定盤中飆股。")
        print("🚀 開始盤中監控...")

        while True:
            now = datetime.datetime.now()
            
            # 【GitHub 專屬修改】：下午 1:30 (13:30) 收盤後，直接終止迴圈讓程式下班
            if now.hour >= 13 and now.minute >= 35:
                print("🏁 股市已收盤，程式自動下班！")
                self.notifier.send_alert("🏁 *今日台股已收盤，監控結束，明天見！*")
                break # 打破迴圈，結束程式
            
            # 09:00 ~ 13:30 正常監控
            if 9 <= now.hour <= 13:
                self.check_and_alert()
            
            time.sleep(interval_seconds)

if __name__ == "__main__":
    TOKEN = "8180918942:AAFXkzX-95J3zQR0l0RcOXVfUO9cyHJaswk" 
    CHAT_ID = "7836204601" 

    tg_bot = TelegramNotifier(bot_token=TOKEN, chat_id=CHAT_ID)
    sniper = LimitUpSniper(notifier=tg_bot)

    try:
        sniper.run_daily_monitor(interval_seconds=15)
    except KeyboardInterrupt:
        print("\n手動停止。")
