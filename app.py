import streamlit as st
from src.agent.orchestrator import run_agent_orchestrator

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="Financial Agentic Assistant",
    page_icon="📈",
    layout="centered"
)

st.title("📈 Financial Agentic Assistant")
st.caption("ระบบวิเคราะห์ข้อมูลหุ้นสหรัฐฯ 10 ตัวด้วย Observe-Think-Act Agent (SQL + SEC 10-K RAG + Python Calc)")

# เก็บ ประวัติ Chat Session
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "สวัสดีครับ! สอบถามข้อมูลตัวเลขงบการเงิน ปัจจัยความเสี่ยง SEC 10-K หรือคำนวณสถิติราคาหุ้นได้เลยครับ"}
    ]

# แสดงข้อความแชทย้อนหลัง
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# ช่องพิมพ์คำถามจากผู้ใช้
if prompt := st.chat_input("พิมพ์คำถามการเงินที่นี่..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🤖 Agent กำลังคิดและเลือกใช้เครื่องมือ..."):
            response = run_agent_orchestrator(prompt)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})