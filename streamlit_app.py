# Streamlitライブラリをインポート
import streamlit as st

# ページ設定（タブに表示されるタイトル、表示幅）
st.set_page_config(page_title="タイトル", layout="wide")

# タイトルを設定
st.title('フィッシング詐欺対策アプリ')
user_name = st.text_input ('あなたの名前を教えてください')
if st.button('挨拶する'):
    if user_name:  # 名前が入力されているかチェック
        st.success(f' こんにちは、{user_name}さん。 今回はどのようなご用件でしょうか')  # メッセージをハイライト
    else:
        st.error('すみません。名前を教えていただけますか。')  # エラーメッセージを表示