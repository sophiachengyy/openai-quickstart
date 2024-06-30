"""
一个简单的demo，调用CharacterGLM实现角色扮演，调用CogView生成图片，调用ChatGLM生成CogView所需的prompt。

依赖：
pyjwt
requests
streamlit
zhipuai
python-dotenv

运行方式：
```bash
streamlit run characterglm_api_demo_streamlit.py
```
"""
import os
import itertools
from typing import Iterator, Optional

import streamlit as st
from dotenv import load_dotenv
# 通过.env文件设置环境变量
# reference: https://github.com/theskumar/python-dotenv
load_dotenv()

import api
from api import generate_chat_scene_prompt, generate_role_appearance, get_characterglm_response, generate_cogview_image
from data_types import TextMsg, ImageMsg, TextMsgList, MsgList, filter_text_msg

st.set_page_config(page_title="CharacterGLM API Demo", page_icon="🤖", layout="wide")
debug = os.getenv("DEBUG", "").lower() in ("1", "yes", "y", "true", "t", "on")


def update_api_key(key: Optional[str] = None):
    if debug:
        print(f'update_api_key. st.session_state["API_KEY"] = {st.session_state["API_KEY"]}, key = {key}')
    key = key or st.session_state["API_KEY"]
    if key:
        api.API_KEY = key

# 设置API KEY
api_key = st.sidebar.text_input("API_KEY", value=os.getenv("API_KEY", ""), key="API_KEY", type="password", on_change=update_api_key)
update_api_key(api_key)


# 初始化
if "history" not in st.session_state:
    st.session_state["history"] = []
if "meta" not in st.session_state:
    st.session_state["meta"] = {
        "bot_name": "黛玉",
        "bot_info": "容颜似蹙非蹙，含情目，病态美，性格敏感细腻，聪慧过人，出身名门，却身世可怜。特征是两弯罥烟眉，闲静如姣花照水，行动处似弱柳扶风，心较比干多一窍，病如西子胜三分。",
        "user_name": "宝玉",
        "user_info": "外表英俊，中秋之月面容，春晓之花色泽，性格叛逆又多情，不拘世俗，生于富贵之家，身佩美玉，具有天然风骚与万种情思。特征是束发嵌宝紫金冠，二龙抢珠金抹额，情感丰富，似傻如狂",
        "image_style": ""
    }


def init_session():
    st.session_state["history"] = []


# 4个输入框，设置meta的4个字段
meta_labels = {
    "bot_name": "角色名",
    "user_name": "用户名", 
    "bot_info": "角色人设",
    "user_info": "用户人设",
    "image_style": "图片风格"
}

# 2x2 layout
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.text_input(label="角色名", key="bot_name", value=st.session_state["meta"]["bot_name"], on_change=lambda : st.session_state["meta"].update(bot_name=st.session_state["bot_name"]), help="模型所扮演的角色的名字，不可以为空")
        st.text_area(label="角色人设", key="bot_info", value=st.session_state["meta"]["bot_info"], on_change=lambda : st.session_state["meta"].update(bot_info=st.session_state["bot_info"]), help="角色的详细人设信息，不可以为空")

    with col2:
        st.text_input(label="用户名", key="user_name", value=st.session_state["meta"]["user_name"], on_change=lambda : st.session_state["meta"].update(user_name=st.session_state["user_name"]), help="用户的名字，默认为用户")
        st.text_area(label="用户人设", key="user_info", value=st.session_state["meta"]["user_info"], on_change=lambda : st.session_state["meta"].update(user_info=st.session_state["user_info"]), help="用户的详细人设信息，可以为空")

    col3 = st.columns(1)
    st.text_input(label="图片风格", value="写实风格", key="image_style",
                  on_change=lambda: st.session_state["meta"].update(image_style=st.session_state["image_style"]),
                  help='''图片的风格，默认为二次元风格。常见的包括但不限于以下几种：
                  
二次元风格:具有动漫或漫画风格。\n
写实风格：追求高度逼真的绘画风格。\n
抽象风格：使用非具象的图形和色彩来表达。\n
印象派风格：模仿印象派画作的特点，如色彩丰富、光影变化等。\n
立体主义风格：采用多重视角和几何化的形状。\n
超现实主义风格：描绘梦境般的场景，追求无逻辑的视觉效果。\n
水墨风格：模仿中国水墨画的风格。\n
像素艺术风格：使用像素化的图形和色彩。\n
版画风格：模仿木刻、铜版画等的效果。\n
装饰艺术风格：注重装饰性和对称性。\n
蒸汽波风格：融合了复古和现代元素，常用粉嫩的色彩和几何图案。''')


def verify_meta() -> bool:
    # 检查`角色名`和`角色人设`是否空，若为空，则弹出提醒
    if st.session_state["meta"]["bot_name"] == "" or st.session_state["meta"]["bot_info"] == "":
        st.error("角色名和角色人设不能为空")
        return False
    else:
        return True


def draw_new_image():
    """生成一张图片，并展示在页面上"""
    if not verify_meta():
        return
    text_messages = filter_text_msg(st.session_state["history"])
    if text_messages:
        # 若有对话历史，则结合角色人设和对话历史生成图片
        image_prompt = "".join(
            generate_chat_scene_prompt(
                text_messages[-10: ],
                meta=st.session_state["meta"]
            )
        )
    else:
        # 若没有对话历史，则根据角色人设生成图片
        image_prompt = "".join(generate_role_appearance(st.session_state["meta"]["bot_info"]))

    if not image_prompt:
        st.error("调用chatglm生成Cogview prompt出错")
        return


    selected_image_style = st.session_state.get("image_style", "二次元风格")

    print(f'image_style: {selected_image_style}')
    image_prompt = f'{selected_image_style}。{image_prompt.strip()}'
    
    print(f"image_prompt = {image_prompt}")

    n_retry = 3
    st.markdown("正在生成图片，请稍等...")
    for i in range(n_retry):
        try:
            img_url = generate_cogview_image(image_prompt)
        except Exception as e:
            if i < n_retry - 1:
                st.error("遇到了一点小问题，重试中...")
            else:
                st.error("又失败啦，点击【生成图片】按钮可再次重试")
                return
        else:
            break
    img_msg = ImageMsg({"role": "image", "image": img_url, "caption": image_prompt})
    # 若history的末尾有图片消息，则替换它，（重新生成）
    # 否则，append（新增）
    while st.session_state["history"] and st.session_state["history"][-1]["role"] == "image":
        st.session_state["history"].pop()
    st.session_state["history"].append(img_msg)
    st.rerun()


button_labels = {
    "clear_meta": "清空人设",
    "clear_history": "清空对话历史",
    "save_history": "保存对话历史",
    "gen_picture": "生成图片"
}
if debug:
    button_labels.update({
        "show_api_key": "查看API_KEY",
        "show_meta": "查看meta",
        "show_history": "查看历史"
    })

# 在同一行排列按钮
with st.container():
    n_button = len(button_labels)
    cols = st.columns(n_button)
    button_key_to_col = dict(zip(button_labels.keys(), cols))
    
    with button_key_to_col["clear_meta"]:
        clear_meta = st.button(button_labels["clear_meta"], key="clear_meta")
        if clear_meta:
            st.session_state["meta"] = {
                "user_info": "",
                "bot_info": "",
                "bot_name": "",
                "user_name": "",
                "image_style": ""
            }
            st.rerun()

    with button_key_to_col["clear_history"]:
        clear_history = st.button(button_labels["clear_history"], key="clear_history")
        if clear_history:
            init_session()
            st.rerun()

    with button_key_to_col["save_history"]:
        save_history = st.button(button_labels["save_history"], key="save_history")
        # if clear_history:
        #     init_session()
        #     st.rerun()
    
    with button_key_to_col["gen_picture"]:
        gen_picture = st.button(button_labels["gen_picture"], key="gen_picture")

    if debug:
        with button_key_to_col["show_api_key"]:
            show_api_key = st.button(button_labels["show_api_key"], key="show_api_key")
            if show_api_key:
                print(f"API_KEY = {api.API_KEY}")
        
        with button_key_to_col["show_meta"]:
            show_meta = st.button(button_labels["show_meta"], key="show_meta")
            if show_meta:
                print(f"meta = {st.session_state['meta']}")
        
        with button_key_to_col["show_history"]:
            show_history = st.button(button_labels["show_history"], key="show_history")
            if show_history:
                print(f"history = {st.session_state['history']}")


# 展示对话历史
for msg in st.session_state["history"]:
    if msg["role"] == "user":
        with st.chat_message(name="user", avatar="user"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message(name="assistant", avatar="assistant"):
            st.markdown(msg["content"])
    elif msg["role"] == "image":
        with st.chat_message(name="assistant", avatar="assistant"):
            st.image(msg["image"], caption=msg.get("caption", None))
    else:
        raise Exception("Invalid role")


if gen_picture:
    draw_new_image()

def save_history_to_file():


    with open('dialog_history.txt', 'w', encoding='utf-8') as file:
        for msg in st.session_state["history"]:
            if msg["role"] == "user":
                with st.chat_message(name="user", avatar="user"):

                    file.write("宝玉："+ msg["content"] + '\n')
            elif msg["role"] == "assistant":
                with st.chat_message(name="assistant", avatar="assistant"):
                    file.write("黛玉："+ msg["content"] + '\n')
            elif msg["role"] == "image":
                with st.chat_message(name="assistant", avatar="assistant"):
                    pass
                    # st.image(msg["image"], caption=msg.get("caption", None))
            else:
                raise Exception("Invalid role")

if save_history:
    save_history_to_file()

with st.chat_message(name="user", avatar="user"):
    input_placeholder = st.empty()
with st.chat_message(name="assistant", avatar="assistant"):
    message_placeholder = st.empty()


def output_stream_response(response_stream: Iterator[str], placeholder):
    content = ""
    for content in itertools.accumulate(response_stream):
        placeholder.markdown(content)
    return content


def start_chat():
    query = st.chat_input("开始对话吧")
    if not query:
        return
    else:
        if not verify_meta():
            return
        if not api.API_KEY:
            st.error("未设置API_KEY")

        input_placeholder.markdown(query)
        st.session_state["history"].append(TextMsg({"role": "user", "content": query}))
        
        response_stream = get_characterglm_response(filter_text_msg(st.session_state["history"]), meta=st.session_state["meta"])
        bot_response = output_stream_response(response_stream, message_placeholder)
        if not bot_response:
            message_placeholder.markdown("生成出错")
            st.session_state["history"].pop()
        else:
            st.session_state["history"].append(TextMsg({"role": "assistant", "content": bot_response}))
            
    
start_chat()
