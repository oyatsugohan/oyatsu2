import streamlit as st
import google.generativeai as genai
import json
import re

# ページ設定
st.set_page_config(
    page_title="フィッシング詐欺検知アプリ",
    page_icon="🛡️",
    layout="wide"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .risk-high {
        background-color: #fee2e2;
        border-left: 5px solid #dc2626;
        padding: 1rem;
        border-radius: 5px;
    }
    .risk-medium {
        background-color: #fef3c7;
        border-left: 5px solid #f59e0b;
        padding: 1rem;
        border-radius: 5px;
    }
    .risk-low {
        background-color: #d1fae5;
        border-left: 5px solid #10b981;
        padding: 1rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ヘッダー
st.markdown("""
<div class="main-header">
    <h1>🛡️ フィッシング詐欺検知アプリ</h1>
    <p>Gemini AIで怪しいURLやメールを分析</p>
</div>
""", unsafe_allow_html=True)

# サイドバー設定
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input(
        "Gemini APIキー",
        type="password",
        help="Google AI StudioでAPIキーを取得: https://makersuite.google.com/app/apikey"
    )
    
    st.markdown("---")
    
    analysis_type = st.radio(
        "分析タイプ",
        ["URL", "メール内容"],
        index=0
    )
    
    st.markdown("---")
    
    st.markdown("""
    ### 📝 使い方
    1. APIキーを入力
    2. 分析タイプを選択
    3. 内容を入力して分析
    
    ### ⚠️ 注意
    - APIキーは安全に管理してください
    - 個人情報は入力しないでください
    """)

# メインコンテンツ
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🔍 分析対象")
    
    if analysis_type == "URL":
        input_text = st.text_area(
            "チェックするURLを入力",
            placeholder="https://example.com",
            height=100
        )
    else:
        input_text = st.text_area(
            "メール本文を入力",
            placeholder="メールの内容を貼り付けてください",
            height=300
        )
    
    analyze_button = st.button("🔎 分析を開始", type="primary", use_container_width=True)

with col2:
    st.header("💡 ヒント")
    if analysis_type == "URL":
        st.info("""
        **チェックポイント:**
        - スペルミスがないか
        - HTTPSかHTTPか
        - ドメインが本物か
        - 短縮URLでないか
        """)
    else:
        st.info("""
        **チェックポイント:**
        - 緊急性を煽っていないか
        - 個人情報を求めていないか
        - 不自然な日本語はないか
        - リンク先が正規サイトか
        """)

# 分析処理
if analyze_button:
    if not api_key:
        st.error("❌ APIキーを入力してください")
    elif not input_text:
        st.error("❌ 分析する内容を入力してください")
    else:
        with st.spinner("🤖 AIが分析中..."):
            try:
                # Gemini API設定
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # プロンプト作成
                if analysis_type == "URL":
                    prompt = f"""以下のURLがフィッシング詐欺サイトである可能性を分析してください。
URL: {input_text}

以下の形式でJSON形式で回答してください：
{{
  "risk_level": "high/medium/low",
  "risk_score": 0-100の数値,
  "is_suspicious": true/false,
  "indicators": ["疑わしい点のリスト"],
  "recommendation": "ユーザーへの推奨アクション",
  "summary": "分析結果の簡潔な要約"
}}"""
                else:
                    prompt = f"""以下のメール内容がフィッシング詐欺である可能性を分析してください。
メール内容:
{input_text}

以下の形式でJSON形式で回答してください：
{{
  "risk_level": "high/medium/low",
  "risk_score": 0-100の数値,
  "is_suspicious": true/false,
  "indicators": ["疑わしい点のリスト"],
  "recommendation": "ユーザーへの推奨アクション",
  "summary": "分析結果の簡潔な要約"
}}"""
                
                # API呼び出し
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.2,
                        max_output_tokens=1000,
                    )
                )
                
                # JSONを抽出
                response_text = response.text
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                
                if json_match:
                    result = json.loads(json_match.group())
                    
                    # 結果表示
                    st.markdown("---")
                    st.header("📊 分析結果")
                    
                    # リスクレベル表示
                    risk_level = result['risk_level']
                    risk_score = result['risk_score']
                    
                    if risk_level == 'high':
                        st.markdown(f'<div class="risk-high"><h2>⚠️ 高リスク ({risk_score}/100)</h2><p>{result["summary"]}</p></div>', unsafe_allow_html=True)
                    elif risk_level == 'medium':
                        st.markdown(f'<div class="risk-medium"><h2>⚡ 中リスク ({risk_score}/100)</h2><p>{result["summary"]}</p></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="risk-low"><h2>✅ 低リスク ({risk_score}/100)</h2><p>{result["summary"]}</p></div>', unsafe_allow_html=True)
                    
                    # プログレスバー
                    st.progress(risk_score / 100)
                    
                    # 詳細情報
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.subheader("🔍 検出された疑わしい点")
                        for i, indicator in enumerate(result['indicators'], 1):
                            st.markdown(f"{i}. {indicator}")
                    
                    with col_b:
                        st.subheader("💡 推奨アクション")
                        st.info(result['recommendation'])
                    
                    # 判定結果
                    if result['is_suspicious']:
                        st.error("🚨 このコンテンツは疑わしいと判定されました。注意してください。")
                    else:
                        st.success("✅ このコンテンツは安全である可能性が高いです。")
                    
                else:
                    st.error("❌ 分析結果の解析に失敗しました")
                    
            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")

# フッター
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>⚠️ このツールは補助的なものです。最終的な判断は慎重に行ってください。</p>
    <p>Powered by Google Gemini AI</p>
</div>
""", unsafe_allow_html=True)
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import re
import hashlib
from datetime import datetime
from urllib.parse import urlparse
import threading
import time
class PhishingProtectionApp:
   def __init__(self, root):
       self.root = root
       self.root.title("🛡️ フィッシング詐欺対策アプリ")
       self.root.geometry("800x600")
       # データベース（本番環境ではファイルやDBに保存）
       self.threat_database = self.load_threat_database()
       self.reported_sites = []
       self.clipboard_history = []
       self.monitoring = False
       self.setup_ui()
   def load_threat_database(self):
       """脅威情報データベースの読み込み"""
       return {
           "dangerous_domains": [
               "paypal-secure-login.com",
               "amazon-verify.net",
               "apple-support-id.com",
               "microsoft-security.net",
               "google-verify-account.com"
           ],
           "suspicious_keywords": [
               "verify account", "urgent action", "suspended",
               "confirm identity", "アカウント確認", "緊急",
               "本人確認", "パスワード更新", "セキュリティ警告"
           ],
           "dangerous_patterns": [
               r"http://[^/]*\.(tk|ml|ga|cf|gq)",  # 無料ドメイン
               r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}",  # IPアドレス
               r"https?://[^/]*-[^/]*(login|signin|verify)",  # ハイフン付きログイン
           ]
       }
   def setup_ui(self):
       """UI構築"""
       # タブの作成
       notebook = ttk.Notebook(self.root)
       notebook.pack(fill='both', expand=True, padx=10, pady=10)
       # タブ1: URL/メールチェック
       self.tab_check = ttk.Frame(notebook)
       notebook.add(self.tab_check, text="🔍 URLチェック")
       self.setup_check_tab()
       # タブ2: リアルタイム監視
       self.tab_monitor = ttk.Frame(notebook)
       notebook.add(self.tab_monitor, text="👁️ リアルタイム監視")
       self.setup_monitor_tab()
       # タブ3: 通報・共有
       self.tab_report = ttk.Frame(notebook)
       notebook.add(self.tab_report, text="📢 通報・共有")
       self.setup_report_tab()
       # タブ4: 脅威情報
       self.tab_threats = ttk.Frame(notebook)
       notebook.add(self.tab_threats, text="⚠️ 脅威情報")
       self.setup_threats_tab()
       # ステータスバー
       self.status_bar = tk.Label(
           self.root,
           text="準備完了",
           bd=1,
           relief=tk.SUNKEN,
           anchor=tk.W
       )
       self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
   def setup_check_tab(self):
       """URLチェックタブの構築"""
       frame = ttk.Frame(self.tab_check, padding="20")
       frame.pack(fill='both', expand=True)
       # タイトル
       title = tk.Label(
           frame,
           text="URLまたはメール内容をチェック",
           font=("Arial", 16, "bold")
       )
       title.pack(pady=10)
       # 入力エリア
       tk.Label(frame, text="チェックしたいURL・メール内容:").pack(anchor='w', pady=5)
       self.check_input = scrolledtext.ScrolledText(frame, height=8, width=70)
       self.check_input.pack(pady=5)
       # チェックボタン
       btn_frame = tk.Frame(frame)
       btn_frame.pack(pady=10)
       ttk.Button(
           btn_frame,
           text="🔍 URLをチェック",
           command=self.check_url
       ).pack(side='left', padx=5)
       ttk.Button(
           btn_frame,
           text="📧 メール内容をチェック",
           command=self.check_email
       ).pack(side='left', padx=5)
       # 結果表示エリア
       tk.Label(frame, text="チェック結果:").pack(anchor='w', pady=5)
       self.result_text = scrolledtext.ScrolledText(
           frame,
           height=12,
           width=70,
           state='disabled'
       )
       self.result_text.pack(pady=5)
   def setup_monitor_tab(self):
       """リアルタイム監視タブの構築"""
       frame = ttk.Frame(self.tab_monitor, padding="20")
       frame.pack(fill='both', expand=True)
       title = tk.Label(
           frame,
           text="クリップボード監視",
           font=("Arial", 16, "bold")
       )
       title.pack(pady=10)
       # 監視制御
       control_frame = tk.Frame(frame)
       control_frame.pack(pady=10)
       self.monitor_btn = ttk.Button(
           control_frame,
           text="🟢 監視開始",
           command=self.toggle_monitoring
       )
       self.monitor_btn.pack(side='left', padx=5)
       self.monitor_status = tk.Label(
           control_frame,
           text="停止中",
           fg="red"
       )
       self.monitor_status.pack(side='left', padx=10)
       # 説明
       info = tk.Label(
           frame,
           text="クリップボードにコピーされた内容を監視し、\n"
                "クレジットカード番号やパスワードなどの機密情報を検知します。",
           fg="gray"
       )
       info.pack(pady=10)
       # 監視ログ
       tk.Label(frame, text="監視ログ:").pack(anchor='w', pady=5)
       self.monitor_log = scrolledtext.ScrolledText(
           frame,
           height=15,
           width=70,
           state='disabled'
       )
       self.monitor_log.pack(pady=5)
   def setup_report_tab(self):
       """通報・共有タブの構築"""
       frame = ttk.Frame(self.tab_report, padding="20")
       frame.pack(fill='both', expand=True)
       title = tk.Label(
           frame,
           text="怪しいサイト・メールを通報",
           font=("Arial", 16, "bold")
       )
       title.pack(pady=10)
       # 通報フォーム
       tk.Label(frame, text="URL:").pack(anchor='w', pady=5)
       self.report_url = tk.Entry(frame, width=60)
       self.report_url.pack(pady=5)
       tk.Label(frame, text="詳細情報:").pack(anchor='w', pady=5)
       self.report_detail = scrolledtext.ScrolledText(frame, height=8, width=70)
       self.report_detail.pack(pady=5)
       ttk.Button(
           frame,
           text="📢 通報する",
           command=self.submit_report
       ).pack(pady=10)
       # 通報履歴
       tk.Label(frame, text="最近の通報情報:").pack(anchor='w', pady=5)
       self.report_list = scrolledtext.ScrolledText(
           frame,
           height=10,
           width=70,
           state='disabled'
       )
       self.report_list.pack(pady=5)
   def setup_threats_tab(self):
       """脅威情報タブの構築"""
       frame = ttk.Frame(self.tab_threats, padding="20")
       frame.pack(fill='both', expand=True)
       title = tk.Label(
           frame,
           text="最新の脅威情報",
           font=("Arial", 16, "bold")
       )
       title.pack(pady=10)
       # 更新ボタン
       btn_frame = tk.Frame(frame)
       btn_frame.pack(pady=10)
       ttk.Button(
           btn_frame,
           text="🔄 データベース更新",
           command=self.update_threat_database
       ).pack(side='left', padx=5)
       self.last_update = tk.Label(
           btn_frame,
           text=f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
       )
       self.last_update.pack(side='left', padx=10)
       # 脅威情報表示
       tk.Label(frame, text="危険なドメインリスト:").pack(anchor='w', pady=5)
       self.threat_list = scrolledtext.ScrolledText(
           frame,
           height=18,
           width=70,
           state='disabled'
       )
       self.threat_list.pack(pady=5)
       self.display_threats()
   def check_url(self):
       """URL安全性チェック"""
       url = self.check_input.get("1.0", tk.END).strip()
       if not url:
           messagebox.showwarning("警告", "URLを入力してください")
           return
       result = self.analyze_url(url)
       self.display_result(result)
   def analyze_url(self, url):
       """URL解析"""
       results = {
           "url": url,
           "risk_level": "安全",
           "warnings": [],
           "details": []
       }
       # ドメイン抽出
       try:
           parsed = urlparse(url)
           domain = parsed.netloc.lower()
           # 危険ドメインチェック
           if any(d in domain for d in self.threat_database["dangerous_domains"]):
               results["risk_level"] = "危険"
               results["warnings"].append("⚠️ 既知の詐欺サイトです！")
           # パターンマッチング
           for pattern in self.threat_database["dangerous_patterns"]:
               if re.search(pattern, url):
                   if results["risk_level"] == "安全":
                       results["risk_level"] = "注意"
                   results["warnings"].append(f"⚠️ 疑わしいURLパターンを検出")
           # HTTPSチェック
           if parsed.scheme != "https":
               results["warnings"].append("⚠️ HTTPSではありません（暗号化されていません）")
               if results["risk_level"] == "安全":
                   results["risk_level"] = "注意"
           # 詳細情報
           results["details"].append(f"ドメイン: {domain}")
           results["details"].append(f"プロトコル: {parsed.scheme}")
           results["details"].append(f"パス: {parsed.path or '/'}")
       except Exception as e:
           results["risk_level"] = "エラー"
           results["warnings"].append(f"❌ URL解析エラー: {str(e)}")
       return results
   def check_email(self):
       """メール内容チェック"""
       content = self.check_input.get("1.0", tk.END).strip()
       if not content:
           messagebox.showwarning("警告", "メール内容を入力してください")
           return
       result = self.analyze_email(content)
       self.display_result(result)
   def analyze_email(self, content):
       """メール内容解析"""
       results = {
           "risk_level": "安全",
           "warnings": [],
           "details": []
       }
       # キーワードチェック
       found_keywords = []
       for keyword in self.threat_database["suspicious_keywords"]:
           if keyword.lower() in content.lower():
               found_keywords.append(keyword)
       if found_keywords:
           results["risk_level"] = "注意"
           results["warnings"].append(f"⚠️ 疑わしいキーワード検出: {', '.join(found_keywords)}")
       # URLチェック
       urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content)
       if urls:
           results["details"].append(f"検出されたURL数: {len(urls)}")
           for url in urls[:3]:  # 最初の3つのみチェック
               url_result = self.analyze_url(url)
               if url_result["risk_level"] in ["危険", "注意"]:
                   results["risk_level"] = "危険" if url_result["risk_level"] == "危険" else "注意"
                   results["warnings"].append(f"⚠️ 危険なURL発見: {url}")
       return results
   def display_result(self, result):
       """結果表示"""
       self.result_text.config(state='normal')
       self.result_text.delete("1.0", tk.END)
       # リスクレベル
       risk_colors = {
           "安全": "green",
           "注意": "orange",
           "危険": "red",
           "エラー": "gray"
       }
       risk_emoji = {
           "安全": "✅",
           "注意": "⚠️",
           "危険": "🚨",
           "エラー": "❌"
       }
       self.result_text.insert(tk.END, f"\n{risk_emoji[result['risk_level']]} ", )
       self.result_text.insert(tk.END, f"リスクレベル: {result['risk_level']}\n\n", )
       # 警告
       if result["warnings"]:
           self.result_text.insert(tk.END, "【警告】\n")
           for warning in result["warnings"]:
               self.result_text.insert(tk.END, f"{warning}\n")
           self.result_text.insert(tk.END, "\n")
       # 詳細
       if result["details"]:
           self.result_text.insert(tk.END, "【詳細情報】\n")
           for detail in result["details"]:
               self.result_text.insert(tk.END, f"• {detail}\n")
       self.result_text.config(state='disabled')
   def toggle_monitoring(self):
       """監視の開始/停止"""
       self.monitoring = not self.monitoring
       if self.monitoring:
           self.monitor_btn.config(text="🔴 監視停止")
           self.monitor_status.config(text="監視中", fg="green")
           self.log_message("クリップボード監視を開始しました")
           threading.Thread(target=self.monitor_clipboard, daemon=True).start()
       else:
           self.monitor_btn.config(text="🟢 監視開始")
           self.monitor_status.config(text="停止中", fg="red")
           self.log_message("クリップボード監視を停止しました")
   def monitor_clipboard(self):
       """クリップボード監視（シミュレーション）"""
       # 実際の実装ではpyperclipなどを使用
       # ここではデモ用のシミュレーション
       last_content = ""
       while self.monitoring:
           try:
               # シミュレーション: ランダムにテストデータ
               # 実際は: current_content = pyperclip.paste()
               time.sleep(2)
               # デモ用の検知例
               test_patterns = [
                   ("1234-5678-9012-3456", "クレジットカード番号"),
                   ("password123", "パスワード"),
                   ("user@example.com", "メールアドレス")
               ]
               # 実際の監視ロジックをここに実装
           except Exception as e:
               self.log_message(f"エラー: {str(e)}")
           time.sleep(1)
   def detect_sensitive_info(self, text):
       """機密情報検出"""
       patterns = {
           "クレジットカード": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
           "パスワード": r'password|passwd|pwd',
           "メールアドレス": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
       }
       detected = []
       for name, pattern in patterns.items():
           if re.search(pattern, text, re.IGNORECASE):
               detected.append(name)
       return detected
   def log_message(self, message):
       """ログメッセージ追加"""
       timestamp = datetime.now().strftime("%H:%M:%S")
       self.monitor_log.config(state='normal')
       self.monitor_log.insert(tk.END, f"[{timestamp}] {message}\n")
       self.monitor_log.see(tk.END)
       self.monitor_log.config(state='disabled')
   def submit_report(self):
       """通報送信"""
       url = self.report_url.get().strip()
       detail = self.report_detail.get("1.0", tk.END).strip()
       if not url:
           messagebox.showwarning("警告", "URLを入力してください")
           return
       report = {
           "url": url,
           "detail": detail,
           "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "reporter": "匿名ユーザー"
       }
       self.reported_sites.append(report)
       # 通報履歴に追加
       self.report_list.config(state='normal')
       self.report_list.insert(
           tk.END,
           f"[{report['timestamp']}] {report['url']}\n詳細: {report['detail'][:50]}...\n\n"
       )
       self.report_list.see(tk.END)
       self.report_list.config(state='disabled')
       # フォームクリア
       self.report_url.delete(0, tk.END)
       self.report_detail.delete("1.0", tk.END)
       messagebox.showinfo("完了", "通報ありがとうございます！\n情報は他のユーザーと共有されます。")
       self.status_bar.config(text=f"通報を受け付けました - {url}")
   def update_threat_database(self):
       """脅威情報データベース更新"""
       # 実際の実装では外部APIから取得
       self.status_bar.config(text="データベースを更新中...")
       self.root.update()
       # シミュレーション
       time.sleep(1)
       # 通報された情報を追加
       for report in self.reported_sites:
           domain = urlparse(report['url']).netloc
           if domain and domain not in self.threat_database["dangerous_domains"]:
               self.threat_database["dangerous_domains"].append(domain)
       self.last_update.config(
           text=f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
       )
       self.display_threats()
       messagebox.showinfo("完了", "脅威情報データベースを更新しました！")
       self.status_bar.config(text="データベース更新完了")
   def display_threats(self):
       """脅威情報表示"""
       self.threat_list.config(state='normal')
       self.threat_list.delete("1.0", tk.END)
       self.threat_list.insert(tk.END, "=== 危険なドメイン ===\n\n")
       for i, domain in enumerate(self.threat_database["dangerous_domains"], 1):
           self.threat_list.insert(tk.END, f"{i}. {domain}\n")
       self.threat_list.insert(tk.END, "\n=== 疑わしいキーワード ===\n\n")
       for i, keyword in enumerate(self.threat_database["suspicious_keywords"], 1):
           self.threat_list.insert(tk.END, f"{i}. {keyword}\n")
       self.threat_list.config(state='disabled')

def main():
   root = tk.Tk()
   app = PhishingProtectionApp(root)
   root.mainloop()

if __name__ == "__main__":
   main()