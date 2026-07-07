论文分析助手 使用说明

简介
---
这是一个轻量的论文分析库，设计用于 Jupyter 笔记本：把论文（PDF 或纯文本）丢进来，能提取标题、作者、摘要、简介、结论、关键词，并生成简短摘要。

安装
---
在虚拟环境中运行：

pip install -r requirements.txt

（可选）若只需基本功能，仅安装 pdfplumber 即可：

pip install pdfplumber

用法（Jupyter 示例）
---
下面的代码片段可直接粘到笔记本中运行：

from paper_analyzer import analyze_paper_from_pdf

# 选择本地 PDF 文件路径
pdf_path = "./example_paper.pdf"

res = analyze_paper_from_pdf(pdf_path)

# 打印主要字段
print('Title:', res.get('title'))
print('Authors:', res.get('authors'))
print('\nAbstract:\n', res.get('abstract')[:1000])
print('\nAuto Summary:\n', res.get('summary'))
print('\nKeywords:', res.get('keywords'))

扩展与提示
---
- 若安装 transformers 并下载模型，摘要质量会更好。
- 对于非英文论文，当前的关键词提取为基于英文的简单频次方法，建议替换为语言适配的 NLP 工具（spaCy、jieba 等）。
- 若论文有严重格式化（两列布局、图表间断），pdfplumber 的文本提取可能需要额外清洗。

下一步
---
已为你生成一个 Streamlit Web UI：运行 streamlit run streamlit_app.py 然后在浏览器中上传 PDF 并点击“分析论文”。

如果你还想要：
- 一个完整的 Jupyter Notebook 示例（交互控件与可视化）
- 将应用部署为公开 Web 服务（用 Streamlit Cloud / Heroku / 自托管）
- 增强的关键词与多语言支持（使用 spaCy / jieba / language-specific tokenizers）

告诉我你希望接着做哪一项。