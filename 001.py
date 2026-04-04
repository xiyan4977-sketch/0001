import requests
import time
import datetime

# ================= 1. Telegram 即时通知模组 =================
class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send_alert(self, message):
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        try:
            response = requests.post(self.base_url, data=payload)
            if response.status_code == 200:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 警报已发送！")
            else:
                print("警报发送失败，请检查 Token 或 Chat ID")
        except Exception as e:
            print(f"网络错误: {e}")

# ================= 2. 多头突破监控策略（附带目标价） =================
class BullBreakoutSniper:
    def __init__(self, notifier):
        self.notifier = notifier
        # 监控清单（70档，可自行增删）
        self.watchlist = [
            {'stock_id': '2330', 'name': '台积电'},
            {'stock_id': '2317', 'name': '鸿海'},
            {'stock_id': '2454', 'name': '联发科'},
            {'stock_id': '2303', 'name': '联电'},
            {'stock_id': '2412', 'name': '中华电'},
            {'stock_id': '2881', 'name': '富邦金'},
            {'stock_id': '2882', 'name': '国泰金'},
            {'stock_id': '2891', 'name': '中信金'},
            {'stock_id': '2886', 'name': '兆丰金'},
            {'stock_id': '2884', 'name': '玉山金'},
            {'stock_id': '2885', 'name': '元大金'},
            {'stock_id': '2892', 'name': '第一金'},
            {'stock_id': '5880', 'name': '合库金'},
            {'stock_id': '1303', 'name': '南亚'},
            {'stock_id': '1326', 'name': '台化'},
            {'stock_id': '1301', 'name': '台塑'},
            {'stock_id': '2002', 'name': '中钢'},
            {'stock_id': '1216', 'name': '统一'},
            {'stock_id': '3045', 'name': '台湾大'},
            {'stock_id': '4904', 'name': '远传'},
            {'stock_id': '2308', 'name': '台达电'},
            {'stock_id': '2382', 'name': '广达'},
            {'stock_id': '3231', 'name': '纬创'},
            {'stock_id': '2356', 'name': '英业达'},
            {'stock_id': '2357', 'name': '华硕'},
            {'stock_id': '2376', 'name': '技嘉'},
            {'stock_id': '2345', 'name': '智邦'},
            {'stock_id': '3034', 'name': '联咏'},
            {'stock_id': '3037', 'name': '欣兴'},
            {'stock_id': '8046', 'name': '南电'},
            {'stock_id': '3189', 'name': '景硕'},
            {'stock_id': '3481', 'name': '群创'},
            {'stock_id': '2409', 'name': '友达'},
            {'stock_id': '3711', 'name': '日月光投控'},
            {'stock_id': '6669', 'name': '纬颖'},
            {'stock_id': '3443', 'name': '创意'},
            {'stock_id': '6531', 'name': '爱普'},
            {'stock_id': '4968', 'name': '立积'},
            {'stock_id': '8016', 'name': '矽创'},
            {'stock_id': '6415', 'name': '矽力-KY'},
            {'stock_id': '5269', 'name': '祥硕'},
            {'stock_id': '3008', 'name': '大立光'},
            {'stock_id': '2498', 'name': '宏达电'},
            {'stock_id': '2912', 'name': '统一超'},
            {'stock_id': '2915', 'name': '润泰全'},
            {'stock_id': '9945', 'name': '润泰新'},
            {'stock_id': '1101', 'name': '台泥'},
            {'stock_id': '1102', 'name': '亚泥'},
            {'stock_id': '1402', 'name': '远东新'},
            {'stock_id': '1476', 'name': '儒鸿'},
            {'stock_id': '2207', 'name': '和泰车'},
            {'stock_id': '2301', 'name': '光宝科'},
            {'stock_id': '2327', 'name': '国巨'},
            {'stock_id': '2379', 'name': '瑞昱'},
            {'stock_id': '2385', 'name': '群光'},
            {'stock_id': '2395', 'name': '研华'},
            {'stock_id': '2408', 'name': '南亚科'},
            {'stock_id': '2449', 'name': '京元电子'},
            {'stock_id': '3035', 'name': '智原'},
            {'stock_id': '3105', 'name': '稳懋'},
            {'stock_id': '3533', 'name': '嘉泽'},
            {'stock_id': '3653', 'name': '健策'},
            {'stock_id': '3661', 'name': '世芯-KY'},
            {'stock_id': '4763', 'name': '材料-KY'},
            {'stock_id': '5274', 'name': '信骅'},
            {'stock_id': '5483', 'name': '中美晶'},
            {'stock_id': '6176', 'name': '瑞仪'},
            {'stock_id': '6269', 'name': '台郡'},
            {'stock_id': '6271', 'name': '同欣电'},
            {'stock_id': '6789', 'name': '采钰'},
        ]
        # 记录已经触发过的股票，避免重复发送
        self.triggered_stocks = set()

    def get_realtime_price(self, stock_id):
        """
        取得台股即时报价（证交所 API）
        """
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_id}.tw&json=1&delay=0"
        try:
            res = requests.get(url + f"&_={int(time.time() * 1000)}", timeout=5)
            data = res.json()
            if data['msgArray']:
                info = data['msgArray'][0]
                return {
                    'current_price': float(info['z']) if info['z'] != '-' else None,
                    'open_price': float(info['o']) if info['o'] != '-' else None,
                    'yesterday_close': float(info['y'])
                }
        except Exception as e:
            print(f"API 错误 ({stock_id}): {e}")
        return None

    def calculate_target_price(self, open_price, yesterday_close):
        """
        简易目标价计算：开盘价 + (开盘价 - 昨收) → 等幅上涨满足点
        可依需求修改为其他技术分析目标
        """
        if open_price is None or yesterday_close is None:
            return None
        return round(open_price + (open_price - yesterday_close), 2)

    def check_and_alert(self):
        """
        单次检查所有股票，若符合「多头突破」条件且尚未触发过，则发送警报（内含目标价）
        多头条件：开红（开盘 > 昨收） 且 现价 > 开盘价（突破开盘价）
        """
        for stock in self.watchlist:
            stock_id = stock['stock_id']
            stock_name = stock['name']

            if stock_id in self.triggered_stocks:
                continue

            price_info = self.get_realtime_price(stock_id)
            if not price_info or price_info['current_price'] is None:
                continue

            current = price_info['current_price']
            open_p = price_info['open_price']
            y_close = price_info['yesterday_close']

            if open_p is None or y_close is None:
                continue

            # 多头条件：开红 + 现价突破开盘价（往上走）
            if open_p > y_close and current > open_p:
                target_price = self.calculate_target_price(open_p, y_close)
                change_from_open = ((current - open_p) / open_p) * 100
                change_from_yest = ((current - y_close) / y_close) * 100

                msg = (
                    f"🚀 *多头突破警报* 🚀\n"
                    f"标的：{stock_name} ({stock_id})\n"
                    f"状态：*开高走高，突破开盘价！*\n"
                    f"昨收：{y_close:.2f}\n"
                    f"开盘：{open_p:.2f}\n"
                    f"现价：{current:.2f} (较开盘 +{change_from_open:.2f}% | 较昨收 +{change_from_yest:.2f}%)\n"
                    f"🎯 *目标价*：{target_price:.2f}\n"
                    f"👉 *操作建议*：多头动能强劲，可考虑短线做多，目标价附近分批获利。"
                )
                self.notifier.send_alert(msg)
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 已触发 {stock_name} 的多头警报！")
                self.triggered_stocks.add(stock_id)

    def run_continuous_monitor(self, interval_seconds=10):
        """
        持续监控，每隔 interval_seconds 秒检查一次
        """
        print("🚀 开始持续监控（多头突破警报 + 目标价）...")
        self.notifier.send_alert("🔔 *监控系统启动*\n系统将每隔 10 秒检查一次，仅当股票出现「开高走高」多头讯号时发送警报，并附带目标价。")

        while True:
            self.check_and_alert()
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 等待 {interval_seconds} 秒后再次检查...")
            time.sleep(interval_seconds)

# ================= 3. 主程序执行区 =================
if __name__ == "__main__":
    # 请在这里填入你的 Telegram Bot Token 和 Chat ID
    TOKEN = "8180918942:AAFXkzX-95J3zQR0l0RcOXVfUO9cyHJaswk" # 请替换成自己的
    CHAT_ID = "7836204601" # 请替换成自己的

    tg_bot = TelegramNotifier(bot_token=TOKEN, chat_id=CHAT_ID)
    sniper = BullBreakoutSniper(notifier=tg_bot)

    try:
        sniper.run_continuous_monitor(interval_seconds=10)
    except KeyboardInterrupt:
        print("\n使用者手动停止监控。")
        sniper.notifier.send_alert("🔴 *监控系统已关闭*")
