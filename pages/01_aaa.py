import streamlit as st
import google.generativeai as genai
import json
import re
from datetime import datetime
from urllib.parse import urlparse
import time

# ページ設定
st.set_page_config(
    page_title="フィッシング詐欺検知アプリ",
    page_icon="🛡️",
    layout="wide"
)

# セッション状態の初期化
if 'threat_database' not in st.session_state:
    st.session_state.threat_database = {
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
            r"http://[^/]*\.(tk|ml|ga|cf|gq)",
            r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}",
            r"https?://[^/]*-[^/]*(login|signin|verify)",
        ]
    }

if 'reported_sites' not in st.session_state:
    st.session_state.reported_sites = []

if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
        margin: 1rem 0;
    }
    .risk-medium {
        background-color: #fef3c7;
        border-left: 5px solid #f59e0b;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .risk-low {
        background-color: #d1fae5;
        border-left: 5px solid #10b981;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .threat-item {
        background-color: #f9fafb;
        padding: 0.5rem;
        margin: 0.3rem 0;
        border-radius: 3px;
        border-left: 3px solid #6366f1;
    }
</style>
""", unsafe_allow_html=True)

# ヘッダー
st.markdown("""
<div class="main-header">
    <h1>🛡️ フィッシング詐欺検知アプリ</h1>
    <p>AIと脅威データベースで怪しいURLやメールを分析</p>
</div>
""", unsafe_allow_html=True)

# サイドバー
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input(
        "Gemini APIキー（オプション）",
        type="password",
        help="AI分析を使用する場合は入力してください: https://makersuite.google.com/app/apikey"
    )
    
    st.markdown("---")
    
    st.markdown("""
    ### 📝 機能
    - **URLチェック**: URL安全性分析
    - **メールチェック**: メール内容分析
    - **ローカル分析**: データベースベース
    - **AI分析**: Gemini活用（要APIキー）
    - **通報機能**: 怪しいサイト共有
    - **脅威情報**: 最新データベース
    
    ### ⚠️ 注意
    - APIキーは安全に管理
    - 個人情報は入力禁止
    - 最終判断は慎重に
    """)

# メインタブ
tab1, tab2, tab3, tab4 = st.tabs(["🔍 URLチェック", "📧 メールチェック", "📢 通報・共有", "⚠️ 脅威情報"])

# URLチェック関数
def analyze_url_local(url):
    """ローカルデータベースでURL解析"""
    results = {
        "url": url,
        "risk_level": "安全",
        "risk_score": 10,
        "warnings": [],
        "details": []
    }
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if not domain:
            results["risk_level"] = "エラー"
            results["risk_score"] = 0
            results["warnings"].append("❌ 有効なURLではありません")
            return results
        
        # 危険ドメインチェック
        if any(d in domain for d in st.session_state.threat_database["dangerous_domains"]):
            results["risk_level"] = "危険"
            results["risk_score"] = 95
            results["warnings"].append("⚠️ 既知の詐欺サイトです！直ちにアクセスを中止してください")
        
        # パターンマッチング
        for pattern in st.session_state.threat_database["dangerous_patterns"]:
            if re.search(pattern, url):
                if results["risk_level"] == "安全":
                    results["risk_level"] = "注意"
                    results["risk_score"] = 60
                results["warnings"].append(f"⚠️ 疑わしいURLパターンを検出")
                break
        
        # HTTPSチェック
        if parsed.scheme == "http":
            results["warnings"].append("⚠️ HTTPSではありません（通信が暗号化されていません）")
            if results["risk_level"] == "安全":
                results["risk_level"] = "注意"
                results["risk_score"] = 40
        
        # 短縮URLチェック
        short_domains = ["bit.ly", "tinyurl.com", "t.co", "goo.gl"]
        if any(s in domain for s in short_domains):
            results["warnings"].append("ℹ️ 短縮URLです。実際のリンク先を確認してください")
        
        # 詳細情報
        results["details"].append(f"ドメイン: {domain}")
        results["details"].append(f"プロトコル: {parsed.scheme}")
        results["details"].append(f"パス: {parsed.path or '/'}")
        
    except Exception as e:
        results["risk_level"] = "エラー"
        results["risk_score"] = 0
        results["warnings"].append(f"❌ URL解析エラー: {str(e)}")
    
    return results

def analyze_email_local(content):
    """ローカルデータベースでメール解析"""
    results = {
        "risk_level": "安全",
        "risk_score": 10,
        "warnings": [],
        "details": []
    }
    
    # キーワードチェック
    found_keywords = []
    for keyword in st.session_state.threat_database["suspicious_keywords"]:
        if keyword.lower() in content.lower():
            found_keywords.append(keyword)
    
    if found_keywords:
        results["risk_level"] = "注意"
        results["risk_score"] = 50
        results["warnings"].append(f"⚠️ 疑わしいキーワード検出: {', '.join(found_keywords[:3])}")
    
    # URLチェック
    urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content)
    if urls:
        results["details"].append(f"検出されたURL数: {len(urls)}")
        dangerous_urls = []
        for url in urls[:5]:
            url_result = analyze_url_local(url)
            if url_result["risk_level"] == "危険":
                results["risk_level"] = "危険"
                results["risk_score"] = 90
                dangerous_urls.append(url)
            elif url_result["risk_level"] == "注意" and results["risk_level"] != "危険":
                results["risk_level"] = "注意"
                results["risk_score"] = max(results["risk_score"], 60)
        
        if dangerous_urls:
            results["warnings"].append(f"🚨 危険なURL発見: {len(dangerous_urls)}件")
    
    # 緊急性チェック
    urgent_words = ["今すぐ", "直ちに", "24時間以内", "immediately", "urgent"]
    if any(word in content.lower() for word in urgent_words):
        results["warnings"].append("⚠️ 緊急性を煽る表現が含まれています")
        results["risk_score"] = min(results["risk_score"] + 20, 100)
    
    return results

# タブ1: URLチェック
with tab1:
    st.header("🔍 URL安全性チェック")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        url_input = st.text_area(
            "チェックするURLを入力",
            placeholder="https://example.com",
            height=100
        )
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            local_check = st.button("🔍 ローカル分析", type="primary", use_container_width=True)
        with col_btn2:
            ai_check = st.button("🤖 AI分析", use_container_width=True)
    
    with col2:
        st.info("""
        **チェックポイント:**
        - スペルミスがないか
        - HTTPSかHTTPか
        - ドメインが本物か
        - 短縮URLでないか
        - 既知の詐欺サイトか
        """)
    
    # ローカル分析
    if local_check and url_input:
        with st.spinner("🔍 分析中..."):
            result = analyze_url_local(url_input)
            
            st.markdown("---")
            st.subheader("📊 分析結果")
            
            # リスクレベル表示
            if result['risk_level'] == '危険':
                st.markdown(f'<div class="risk-high"><h3>🚨 高リスク ({result["risk_score"]}/100)</h3><p>このURLは危険です！アクセスしないでください。</p></div>', unsafe_allow_html=True)
            elif result['risk_level'] == '注意':
                st.markdown(f'<div class="risk-medium"><h3>⚠️ 中リスク ({result["risk_score"]}/100)</h3><p>注意が必要です。慎重に確認してください。</p></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="risk-low"><h3>✅ 低リスク ({result["risk_score"]}/100)</h3><p>このURLは比較的安全です。</p></div>', unsafe_allow_html=True)
            
            st.progress(result['risk_score'] / 100)
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("⚠️ 警告")
                if result['warnings']:
                    for warning in result['warnings']:
                        st.warning(warning)
                else:
                    st.success("特に問題は検出されませんでした")
            
            with col_b:
                st.subheader("📋 詳細情報")
                for detail in result['details']:
                    st.text(detail)
    
    # AI分析
    if ai_check and url_input:
        if not api_key:
            st.error("❌ AI分析にはGemini APIキーが必要です（サイドバーで設定）")
        else:
            with st.spinner("🤖 AIが分析中..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"""以下のURLがフィッシング詐欺サイトである可能性を分析してください。
URL: {url_input}

以下の形式でJSON形式で回答してください：
{{
  "risk_level": "high/medium/low",
  "risk_score": 0-100の数値,
  "is_suspicious": true/false,
  "indicators": ["疑わしい点のリスト"],
  "recommendation": "ユーザーへの推奨アクション",
  "summary": "分析結果の簡潔な要約"
}}"""
                    
                    response = model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.2,
                            max_output_tokens=1000,
                        )
                    )
                    
                    json_match = re.search(r'\{[\s\S]*\}', response.text)
                    if json_match:
                        result = json.loads(json_match.group())
                        
                        st.markdown("---")
                        st.subheader("📊 AI分析結果")
                        
                        if result['risk_level'] == 'high':
                            st.markdown(f'<div class="risk-high"><h3>🚨 高リスク ({result["risk_score"]}/100)</h3><p>{result["summary"]}</p></div>', unsafe_allow_html=True)
                        elif result['risk_level'] == 'medium':
                            st.markdown(f'<div class="risk-medium"><h3>⚠️ 中リスク ({result["risk_score"]}/100)</h3><p>{result["summary"]}</p></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="risk-low"><h3>✅ 低リスク ({result["risk_score"]}/100)</h3><p>{result["summary"]}</p></div>', unsafe_allow_html=True)
                        
                        st.progress(result['risk_score'] / 100)
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.subheader("🔍 検出された疑わしい点")
                            for i, indicator in enumerate(result['indicators'], 1):
                                st.markdown(f"{i}. {indicator}")
                        
                        with col_b:
                            st.subheader("💡 推奨アクション")
                            st.info(result['recommendation'])
                    else:
                        st.error("❌ 分析結果の解析に失敗しました")
                except Exception as e:
                    st.error(f"❌ エラーが発生しました: {str(e)}")

# タブ2: メールチェック
with tab2:
    st.header("📧 メール内容チェック")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        email_input = st.text_area(
            "メール本文を入力",
            placeholder="メールの内容を貼り付けてください",
            height=300
        )
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            email_local = st.button("🔍 ローカル分析（メール）", type="primary", use_container_width=True)
        with col_btn2:
            email_ai = st.button("🤖 AI分析（メール）", use_container_width=True)
    
    with col2:
        st.info("""
        **チェックポイント:**
        - 緊急性を煽っていないか
        - 個人情報を求めていないか
        - 不自然な日本語はないか
        - リンク先が正規サイトか
        - 疑わしいキーワードがないか
        """)
    
    # ローカル分析
    if email_local and email_input:
        with st.spinner("🔍 分析中..."):
            result = analyze_email_local(email_input)
            
            st.markdown("---")
            st.subheader("📊 分析結果")
            
            if result['risk_level'] == '危険':
                st.markdown(f'<div class="risk-high"><h3>🚨 高リスク ({result["risk_score"]}/100)</h3><p>このメールは詐欺の可能性が高いです！</p></div>', unsafe_allow_html=True)
            elif result['risk_level'] == '注意':
                st.markdown(f'<div class="risk-medium"><h3>⚠️ 中リスク ({result["risk_score"]}/100)</h3><p>注意が必要です。慎重に確認してください。</p></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="risk-low"><h3>✅ 低リスク ({result["risk_score"]}/100)</h3><p>このメールは比較的安全です。</p></div>', unsafe_allow_html=True)
            
            st.progress(result['risk_score'] / 100)
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("⚠️ 警告")
                if result['warnings']:
                    for warning in result['warnings']:
                        st.warning(warning)
                else:
                    st.success("特に問題は検出されませんでした")
            
            with col_b:
                st.subheader("📋 詳細情報")
                for detail in result['details']:
                    st.text(detail)
    
    # AI分析
    if email_ai and email_input:
        if not api_key:
            st.error("❌ AI分析にはGemini APIキーが必要です")
        else:
            with st.spinner("🤖 AIが分析中..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"""以下のメール内容がフィッシング詐欺である可能性を分析してください。
メール内容:
{email_input}

以下の形式でJSON形式で回答してください：
{{
  "risk_level": "high/medium/low",
  "risk_score": 0-100の数値,
  "is_suspicious": true/false,
  "indicators": ["疑わしい点のリスト"],
  "recommendation": "ユーザーへの推奨アクション",
  "summary": "分析結果の簡潔な要約"
}}"""
                    
                    response = model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.2,
                            max_output_tokens=1000,
                        )
                    )
                    
                    json_match = re.search(r'\{[\s\S]*\}', response.text)
                    if json_match:
                        result = json.loads(json_match.group())
                        
                        st.markdown("---")
                        st.subheader("📊 AI分析結果")
                        
                        if result['risk_level'] == 'high':
                            st.markdown(f'<div class="risk-high"><h3>🚨 高リスク ({result["risk_score"]}/100)</h3><p>{result["summary"]}</p></div>', unsafe_allow_html=True)
                        elif result['risk_level'] == 'medium':
                            st.markdown(f'<div class="risk-medium"><h3>⚠️ 中リスク ({result["risk_score"]}/100)</h3><p>{result["summary"]}</p></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="risk-low"><h3>✅ 低リスク ({result["risk_score"]}/100)</h3><p>{result["summary"]}</p></div>', unsafe_allow_html=True)
                        
                        st.progress(result['risk_score'] / 100)
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.subheader("🔍 検出された疑わしい点")
                            for i, indicator in enumerate(result['indicators'], 1):
                                st.markdown(f"{i}. {indicator}")
                        
                        with col_b:
                            st.subheader("💡 推奨アクション")
                            st.info(result['recommendation'])
                except Exception as e:
                    st.error(f"❌ エラーが発生しました: {str(e)}")

# タブ3: 通報・共有
with tab3:
    st.header("📢 怪しいサイト・メールを通報")
    
    with st.form("report_form"):
        report_url = st.text_input("URL", placeholder="https://suspicious-site.com")
        report_detail = st.text_area("詳細情報", placeholder="どのような詐欺の疑いがあるか説明してください", height=150)
        submitted = st.form_submit_button("📢 通報する", type="primary")
        
        if submitted:
            if report_url:
                report = {
                    "url": report_url,
                    "detail": report_detail,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.reported_sites.append(report)
                st.success("✅ 通報ありがとうございます！情報はデータベースに追加されました。")
            else:
                st.error("❌ URLを入力してください")
    
    st.markdown("---")
    st.subheader("📋 最近の通報情報")
    
    if st.session_state.reported_sites:
        for i, report in enumerate(reversed(st.session_state.reported_sites[-10:]), 1):
            with st.expander(f"🚨 通報 #{len(st.session_state.reported_sites) - i + 1} - {report['url'][:50]}..."):
                st.text(f"日時: {report['timestamp']}")
                st.text(f"URL: {report['url']}")
                st.text(f"詳細: {report['detail']}")
    else:
        st.info("まだ通報はありません")

# タブ4: 脅威情報
with tab4:
    st.header("⚠️ 脅威情報データベース")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text(f"最終更新: {st.session_state.last_update}")
    with col2:
        if st.button("🔄 更新", use_container_width=True):
            # 通報されたサイトをデータベースに追加
            for report in st.session_state.reported_sites:
                domain = urlparse(report['url']).netloc
                if domain and domain not in st.session_state.threat_database["dangerous_domains"]:
                    st.session_state.threat_database["dangerous_domains"].append(domain)
            
            st.session_state.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success("✅ データベースを更新しました！")
            time.sleep(1)
            st.rerun()
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚫 危険なドメイン")
        for i, domain in enumerate(st.session_state.threat_database["dangerous_domains"], 1):
            st.markdown(f'<div class="threat-item">{i}. {domain}</div>', unsafe_allow_html=True)
    
    with col2:
        st.subheader("🔍 疑わしいキーワード")
        for i, keyword in enumerate(st.session_state.threat_database["suspicious_keywords"], 1):
            st.markdown(f'<div class="threat-item">{i}. {keyword}</div>', unsafe_allow_html=True)

# フッター
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>⚠️ このツールは補助的なものです。最終的な判断は慎重に行ってください。</p>
    <p>💡 ローカル分析は無料、AI分析にはGemini APIキーが必要です</p>
    <p>Powered by Google Gemini AI & Local Threat Database</p>
</div>
""", unsafe_allow_html=True)