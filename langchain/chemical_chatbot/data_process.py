import re
from langchain.text_splitter import CharacterTextSplitter

import fitz
def extract_text_with_pymupdf(pdf_path):
    document = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text()
    return text
def preprocess_text(text):
    # 清理特殊字符和多余空白
    text = re.sub(r'\u3000', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    return text


def split_text_by_chapters(text, chapters):
    # 根据目录信息分割文本
    chapter_texts = {}
    for i, chapter in enumerate(chapters):
        start_pos = text.find(chapter)
        if i < len(chapters) - 1:
            end_pos = text.find(chapters[i + 1])
            chapter_texts[chapter] = text[start_pos:end_pos]
        else:
            chapter_texts[chapter] = text[start_pos:]
    return chapter_texts


def process_textbook(extracted_text, chapters):
    preprocessed_text = preprocess_text(extracted_text)
    chapter_texts = split_text_by_chapters(preprocessed_text, chapters)

    docs = []
    text_splitter = CharacterTextSplitter(
        separator=r'[。？！]',  # 按换行符分割
        chunk_size=1000,  # 每个块的大小
        chunk_overlap=100,  # 块之间的重叠部分
        length_function=len,
        is_separator_regex=True,
    )

    for chapter, text in chapter_texts.items():
        chapter_docs = text_splitter.create_documents([text])
        docs.extend(chapter_docs)

    return docs


# 假设你有从PDF中提取的文本
extracted_text = extracted_text = extract_text_with_pymupdf("data/textbook/chemical_1.pdf")
extracted_text=extracted_text.replace('\u3000', '').replace('\u2003',' ').replace('\n', '')


# 课本的目录
chapters = [
    "1.1 物质的分类",
    "1.2 物质的量",
    "1.3 化学中常用的实验方法",
    "本章复习",
    "项目学习活动 如何测定气体摩尔体积",
    "2.1 海水中的氯",
    "2.2 氧化还原反应和离子反应",
    "2.3 溴和碘的提取",
    "本章复习",
    "3. 硫酸盐",
    "3.1 硫及其重要化合物",
    "3.2 氮及其重要化合物",
    "3.3 硫循环和氮循环",
    "本章复习",
    "项目学习活动 如何测定硫酸铜晶体中结晶水的含量",
    "4.1 元素周期表和元素周期律",
    "4.2 原子结构",
    "4.3 核外电子排布",
    "4.4 化学键",
    "本章复习"
]

# 处理课本文档
docs1 = process_textbook(extracted_text, chapters)


with open("data/chemical_guideline.txt") as f:
    chemical_guideline = f.read()


from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import CharacterTextSplitter
text_splitter = CharacterTextSplitter(
    separator=r'\d+\.',
    chunk_size=100,
    chunk_overlap=0,
    length_function=len,
    is_separator_regex=True,
)
docs2 = text_splitter.create_documents([chemical_guideline])
print(docs2[len(docs2)-1])
print(len(docs2))

docs2.extend(docs1)

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS

db = FAISS.from_documents(docs2, OpenAIEmbeddings())

query = "对绿色化学的考试要求"
answer_list = db.similarity_search(query)
for ans in answer_list:
    print(ans.page_content + "\n")

query2 = "侯氏制碱法"
answer_list = db.similarity_search(query2)
for ans in answer_list:
    print(ans.page_content + "\n")


db.save_local("chemical_knowledge")
# retriever = db.as_retriever(
#     search_type="similarity_score_threshold",
#     search_kwargs={"score_threshold": 0.8}
# )
# docs = retriever.get_relevant_documents(query)
# for doc in docs:
#     print(doc.page_content + "\n")
#
# docs = retriever.get_relevant_documents(query2)
# for doc in docs:
#     print(doc.page_content + "\n")
