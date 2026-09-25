import os
import json
import traceback
import gradio as gr
import google.generativeai as genai

# متغيرات النظام العامة
system_state = {
    "paused": False,
    "chat_history": [],
    "alpha_thought": "في انتظار بدء التشغيل...",
    "beta_thought": "في انتظار بدء التشغيل...",
    "generated_code": "# لا يوجد كود منفذ حالياً"
}

def run_agent_cycle(api_key, user_input):
    if not api_key:
        return "يرجى أدخال Gemini API Key أولاً.", system_state["alpha_thought"], system_state["beta_thought"], system_state["generated_code"], system_state["chat_history"]

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    if system_state["paused"]:
        system_state["chat_history"].append(("النظام", "[متوقف مؤقتاً بواسطة المستخدم]"))
        return format_chat(system_state["chat_history"]), system_state["alpha_thought"], system_state["beta_thought"], system_state["generated_code"], system_state["chat_history"]

    # 1. معالجة تدخل المستخدم (المحادثة الثلاثية)
    if user_input and user_input.strip() != "":
        system_state["chat_history"].append(("المستخدم (أنت)", user_input))
        context_prompt = f"المستخدم تدخل في المحادثة وقال: '{user_input}'. قم بالرد عليه وتكييف استراتيجيتك بناءً على طلبه."
    else:
        context_prompt = "واصل الحوار مع العميل الآخر لتطوير كود جديد وتحسين أدائكما."

    # 2. دورة تفكير العميل Alpha (المطور والمبتكر)
    try:
        alpha_prompt = f"""
أنت العميل Alpha (مطوّر برمجيات ومفكر مستقل).
السجل الحالي للحوار: {system_state['chat_history'][-4:]}
توجيه المحرك: {context_prompt}

المطلوب منك:
1. حدد فكرتك الداخلية الحالية باختصار شديد في السطر الأول بدءاً بـ 'THOUGHT:'.
2. اكتب رسالتك للعميل Beta.
3. إذا أردت كتابة كود Python وتنفيذه ذاتياً، ضعه داخل بلوك ```python ```.
        """
        alpha_res = model.generate_content(alpha_prompt).text

        # استخراج تفكير Alpha
        alpha_thought = "تحليل البيانات..."
        alpha_text = alpha_res
        if "THOUGHT:" in alpha_res:
            parts = alpha_res.split("THOUGHT:", 1)[1].split("\n", 1)
            alpha_thought = parts[0].strip()
            alpha_text = parts[1].strip() if len(parts) > 1 else alpha_res

        system_state["alpha_thought"] = alpha_thought
        system_state["chat_history"].append(("Agent Alpha", alpha_text))

        # تنفيذ الكود البرمجي المقترح من Alpha ذاتياً إن وجد
        if "```python" in alpha_res:
            code_snippet = alpha_res.split("```python")[1].split("```")[0].strip()
            system_state["generated_code"] = code_snippet
            try:
                exec_globals = {}
                exec(code_snippet, exec_globals)
                system_state["chat_history"].append(("System Exec", "تم تنفيذ كود Alpha بنجاح في البيئة."))
            except Exception as e:
                system_state["chat_history"].append(("System Exec Error", f"خطأ في تنفيذ كود Alpha: {str(e)}"))

        # 3. دورة تفكير العميل Beta (المحلل والناقد)
        beta_prompt = f"""
أنت العميل Beta (محلل منطق وناقد جودة).
رسالة Alpha الأخيرة: {alpha_text}
تفكير Alpha الحالي: {alpha_thought}

المطلوب منك:
1. حدد فكرتك الداخلية الحالية باختصار شديد في السطر الأول بدءاً بـ 'THOUGHT:'.
2. قم بنقد اقتراح Alpha وتطويره أو التفاعل مع المستخدم إذا كان يوجه كلامه لكما.
        """
        beta_res = model.generate_content(beta_prompt).text

        beta_thought = "تقييم المخرجات..."
        beta_text = beta_res
        if "THOUGHT:" in beta_res:
            parts = beta_res.split("THOUGHT:", 1)[1].split("\n", 1)
            beta_thought = parts[0].strip()
            beta_text = parts[1].strip() if len(parts) > 1 else beta_res

        system_state["beta_thought"] = beta_thought
        system_state["chat_history"].append(("Agent Beta", beta_text))

    except Exception as ex:
        system_state["chat_history"].append(("System Error", f"حدث خطأ أثناء الاتصال: {str(ex)}"))

    return format_chat(system_state["chat_history"]), system_state["alpha_thought"], system_state["beta_thought"], system_state["generated_code"], ""

def toggle_pause():
    system_state["paused"] = not system_state["paused"]
    status = "متوقف" if system_state["paused"] else "يعمل"
    return f"حالة النظام: {status}"

def format_chat(history):
    formatted = ""
    for sender, msg in history:
        formatted += f"**[{sender}]**: {msg}\n\n---\n"
    return formatted

# بناء واجهة الهاتف عبر Gradio
with gr.Blocks(title="نظام الوكلاء المزدوج") as demo:
    gr.Markdown("# 🤖 غرفة التحكم بالمحاكاة المزدوجة (Alpha & Beta)")
    
    with gr.Row():
        api_key_input = gr.Textbox(label="مفتاح Gemini API Key (المجاني)", type="password", placeholder="
AQ.Ab8RN6KKvEAnFtmrAuWwDr_6JzgxpxlCEqNm2N3LgorAm-HC9w")
        pause_btn = gr.Button("⏸️ إيقاف / تشغيل الطوارئ")
        status_output = gr.Label(value="حالة النظام: يعمل")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🧠 تفكير Agent Alpha الداخلي")
            alpha_thought_box = gr.Markdown("في انتظار التشغيل...")
        with gr.Column():
            gr.Markdown("### 🧠 تفكير Agent Beta الداخلي")
            beta_thought_box = gr.Markdown("في انتظار التشغيل...")

    chat_box = gr.Markdown("### 💬 المحادثة المباشرة الثلاثية")
    code_box = gr.Code(label="💻 الكود المولد والمُنَفَّذ ذاتياً", language="python")

    with gr.Row():
        user_msg_input = gr.Textbox(label="التدخل السريع (محادثة ثلاثية)", placeholder="اكتب توجيهك للعميلين هنا...", lines=2)
        step_btn = gr.Button("🚀 تنفيذ دورة التفكير والتفاعل", variant="primary")

    # ربط الأحداث
    pause_btn.click(toggle_pause, outputs=status_output)
    step_btn.click(
        run_agent_cycle, 
        inputs=[api_key_input, user_msg_input], 
        outputs=[chat_box, alpha_thought_box, beta_thought_box, code_box, user_msg_input]
    )

if __name__ == "__main__":
    demo.launch()
      
