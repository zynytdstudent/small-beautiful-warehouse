"""
streamlit_app.py
Streamlit Web UI for the paper analysis assistant.

Usage: pip install -r requirements.txt
Run: streamlit run streamlit_app.py
"""
import streamlit as st
import json
import tempfile
import os
from paper_analyzer import analyze_paper_from_pdf

st.set_page_config(page_title="Paper Analysis Assistant", layout="wide")
st.title("Paper Analysis Assistant — Streamlit UI")

st.markdown("上传论文 PDF（单文件），按下“分析”按钮可提取标题、作者、摘要、关键词与自动摘要。")

uploaded = st.file_uploader("选择 PDF 文件", type=["pdf"])

if uploaded is not None:
    with st.spinner('正在保存上传的文件...'):
        tmp_dir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp_dir, uploaded.name)
        with open(tmp_path, 'wb') as f:
            f.write(uploaded.getbuffer())
    st.success(f'文件已保存：{uploaded.name}')

    if st.button('分析论文'):
        with st.spinner('正在提取与分析...（可能需要几秒到几十秒）'):
            try:
                result = analyze_paper_from_pdf(tmp_path)
            except Exception as e:
                st.error(f'分析失败：{e}')
                result = None
        if result:
            col1, col2 = st.columns([2,1])
            with col1:
                st.subheader('主要信息')
                st.write('标题:', result.get('title',''))
                st.write('作者:', result.get('authors',''))
                st.markdown('**摘要（原文）**')
                st.write(result.get('abstract','')[:5000])
                st.markdown('**自动摘要**')
                st.write(result.get('summary',''))
                st.markdown('**结论节选**')
                st.write(result.get('conclusion','')[:1500])

                with st.expander('显示全文（截断展示）'):
                    st.text_area('Full text', value=result.get('full_text','')[:200000], height=400)

            with col2:
                st.subheader('关键词')
                kw = result.get('keywords', [])
                if kw:
                    for k in kw:
                        st.button(k)
                else:
                    st.write('未提取到关键词')

                st.subheader('下载')
                json_bytes = json.dumps(result, ensure_ascii=False, indent=2).encode('utf-8')
                st.download_button('下载 JSON', data=json_bytes, file_name='paper_analysis.json', mime='application/json')

            st.success('分析完成')

else:
    st.info('请上传 PDF 文件开始')

st.markdown('---')
st.markdown('建议：对于较长或格式复杂的论文，先在本地用 pdfplumber 检查提取效果，或尝试不同的文本预处理。')