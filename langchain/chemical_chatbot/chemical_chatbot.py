import gradio as gr

from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS


def initialize_chemical_bot(vector_store_dir: str="chemical_knowledge"):
    db = FAISS.load_local(vector_store_dir, OpenAIEmbeddings(),allow_dangerous_deserialization=True)
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    
    global CHEMICAL_BOT
    CHEMICAL_BOT = RetrievalQA.from_chain_type(llm,
                                           retriever=db.as_retriever(search_type="similarity_score_threshold",
                                                                     search_kwargs={"score_threshold": 0.6}))
    # 返回向量数据库的检索结果
    CHEMICAL_BOT.return_source_documents = True

    return CHEMICAL_BOT

def sales_chat(message, history):
    print(f"[message]{message}")
    print(f"[history]{history}")
    # TODO: 从命令行参数中获取
    enable_chat = True

    ans = CHEMICAL_BOT({"query": message})
    # 如果检索出结果，或者开了大模型聊天模式
    # 返回 RetrievalQA combine_documents_chain 整合的结果
    if ans["source_documents"] or enable_chat:
        print(f"[result]{ans['result']}")
        print(f"[source_documents]{ans['source_documents']}")
        return ans["result"]
    # 否则输出套路话术
    else:
        return "这个问题我要问问老师"
    

def launch_gradio():
    demo = gr.ChatInterface(
        fn=sales_chat,
        title="化学大师",
        examples=["什么是氧化还原反应？", "化学键的类型有哪些？","离子式的考试要求是什么？"],
        retry_btn=None,
        undo_btn=None,
        chatbot=gr.Chatbot(height=480),
    )

    demo.launch(share=True, server_name="0.0.0.0")

if __name__ == "__main__":

    # 初始化化学大师机器人
    initialize_chemical_bot()
    # 启动 Gradio 服务
    launch_gradio()
