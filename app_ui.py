# import gradio as gr
# import requests

# FLASK_URL = "http://localhost:8080"

# # =====================================================================
# # API CALL HELPERS
# # =====================================================================
# def submit_text(text, creator_id):
#     if not text.strip() or not creator_id.strip():
#         return "⚠️ Error: Text and Creator ID cannot be blank.", None, gr.update(visible=False)
    
#     try:
#         response = requests.post(f"{FLASK_URL}/submit", json={"text": text, "creator_id": creator_id})
#         if response.status_code == 200:
#             data = response.json()
            
#             # Fetch additional system log records to pull the individual underlying signal dimensions
#             log_response = requests.get(f"{FLASK_URL}/log")
#             s1_score, s2_score = 0.0, 0.0
#             if log_response.status_code == 200:
#                 entries = log_response.json().get("entries", [])
#                 # Match the current active record by UUID context
#                 current_record = next((e for e in entries if e.get("content_id") == data["content_id"]), None)
#                 if current_record:
#                     s1_score = current_record.get("llm_score", 0.0)
#                     s2_score = current_record.get("stylometric_score", 0.0)

#             # Extract clean human-readable header blocks from transparency label
#             raw_label = data['label']
#             if " > " in raw_label:
#                 header, description = raw_label.split(" > ", 1)
#             else:
#                 header, description = "Classification Determined", raw_label

#             # Calculate an explicit confidence percentage from the combined score context
#             raw_confidence = data['confidence']
#             if data['attribution'] == "likely_human":
#                 display_pct = round((1.0 - raw_confidence) * 100)
#             elif data['attribution'] == "likely_ai":
#                 display_pct = round(raw_confidence * 100)
#             else:
#                 display_pct = round((1.0 - abs(0.5 - raw_confidence)) * 100)

#             # Structural Layout Template Formatting
#             ui_markdown_output = f"## **{header}**\n\n"
#             ui_markdown_output += f"{description}\n\n"
#             ui_markdown_output += f"--- \n"
#             ui_markdown_output += f"📊 **Score Analysis:**\n"
#             ui_markdown_output += f"* **Confidence Score:** `{display_pct}%`\n"
#             ui_markdown_output += f"* **Combined Core Score:** `{raw_confidence}`\n"
#             ui_markdown_output += f"* **Signal 1 (Semantic Probabilities):** `{s1_score}`\n"
#             ui_markdown_output += f"* **Signal 2 (Stylometric Heuristics):** `{s2_score}`"

#             return (
#                 ui_markdown_output,
#                 data['content_id'],
#                 gr.update(visible=True)  # Reveal the "Dispute This Result" button next to the labels
#             )
#         elif response.status_code == 429:
#             return "🛑 Rate Limit Exceeded: Please wait a minute before trying again.", None, gr.update(visible=False)
#         else:
#             return f"❌ Error: {response.json().get('error', 'Unknown issue')}", None, gr.update(visible=False)
#     except Exception as e:
#         return f"💥 Connection Error: Is your Flask app running? ({str(e)})", None, gr.update(visible=False)


# def file_appeal(content_id, reasoning):
#     if not content_id:
#         return "⚠️ Error: No active Submission ID found to appeal."
#     if len(reasoning) < 10 or len(reasoning) > 500:
#         return "⚠️ Validation Error: Appeal reasoning must be between 10 and 500 characters."
        
#     try:
#         response = requests.post(f"{FLASK_URL}/appeal", json={"content_id": content_id, "creator_reasoning": reasoning})
#         if response.status_code == 200:
#             return " Appeal submitted successfully! The submission state has transitioned to 'under_review'."
#         else:
#             return f"❌ Appeal Denied: {response.json().get('error', 'Processing failure')}"
#     except Exception as e:
#         return f"💥 Connection Error: {str(e)}"


# def fetch_user_history(creator_id):
#     if not creator_id.strip():
#         return "⚠️ Error: Please enter a valid Creator Handle to look up history."
        
#     try:
#         response = requests.get(f"{FLASK_URL}/log")
#         if response.status_code == 200:
#             entries = response.json().get("entries", [])
            
#             # Filter logs down to matches for this exact creator handle
#             user_entries = [e for e in entries if str(e.get("creator_id")).strip() == creator_id.strip()]
            
#             if not user_entries:
#                 return f"No submission records found for handle: `{creator_id}`"
                
#             # Render out the historical log items as scannable markdown blocks
#             formatted_output = f"## Audit Log for `{creator_id}` ({len(user_entries)} entries found)\n\n"
#             for idx, case in enumerate(reversed(user_entries), 1): # Reversed so newest evaluations appear first
#                 status_emoji = "⏳" if case.get("status") == "under_review" else "✅"
                
#                 formatted_output += f"### {status_emoji} Entry #{idx}: `{case['content_id']}`\n"
#                 formatted_output += f"**Timestamp:** `{case['timestamp']}` | **Status:** `{case['status'].upper()}`\n\n"
#                 formatted_output += f"> **Text Fragment:**\n> \"{case['text_content'][:200]}...\"\n\n" # Truncated for readability
#                 formatted_output += f" **Metrics History:**\n"
#                 formatted_output += f"* Combined Score: `{case['confidence']}` | LLM Signal: `{case['llm_score']}` | Stylometric Signal: `{case['stylometric_score']}`\n"
                
#                 if case.get("appeal_reasoning"):
#                     formatted_output += f"🛡️ **Filed Appeal Reason:** *\"{case['appeal_reasoning']}\"*\n"
#                 formatted_output += "---\n\n"
                
#             return formatted_output
#         return "❌ Failed to fetch structural system logs."
#     except Exception as e:
#         return f" Connection Error: {str(e)}"


# # =====================================================================
# # GRADIO INTERFACE LAYOUT
# # =====================================================================
# with gr.Blocks(title="Provenance Guard Dashboard") as demo:
#     gr.Markdown("# Provenance Guard")
#     gr.Markdown("We analyze text structure and style to verify original human writing, provide clear breakdowns of our reasoning, and offer an instant human review process if you ever want to dispute a result.")
    
#     with gr.Tabs():
#         # TAB 1: CREATOR WORKSPACE
#         with gr.TabItem("Work Evaluation"):
#             gr.Markdown("### Submit Text for Evaluation")
            
#             with gr.Row():
#                 # Left Side: Submissions
#                 with gr.Column(scale=2):
#                     input_creator = gr.Textbox(label="Creator Handle (case-sensitive)", placeholder="e.g., author-44", value="creator-44")
#                     input_text = gr.Textbox(label="Raw Writing Content", placeholder="Paste your text block here...", lines=8)
#                     submit_btn = gr.Button("Submit Entry", variant="primary")
                
#                 # Right Side: Targeted Label Results
#                 with gr.Column(scale=1):
#                     gr.Markdown("### Evaluation Results")
#                     output_label = gr.Markdown("*Awaiting submission text analysis...*")
#                     trigger_appeal_btn = gr.Button("Dispute This Result", variant="secondary", visible=False)
            
#             active_content_id = gr.State()
            
#             # Hidden Input Form: Revealed only when trigger_appeal_btn is explicitly clicked
#             with gr.Group(visible=False) as appeal_box:
#                 gr.Markdown("---")
#                 gr.Markdown("### ⚖️ File a Formal System Appeal")
#                 gr.Markdown("Provide context about your writing background or language patterns to route this record to human verification.")
#                 appeal_reason = gr.Textbox(label="Your Explanation Statement (10-500 characters)", placeholder="Why is this evaluation inaccurate?...")
#                 appeal_btn = gr.Button("Submit Official Appeal", variant="stop")
#                 appeal_status = gr.Markdown()

#             # =====================================================================
#             # EVENT WIRING MACHINE (TAB 1)
#             # =====================================================================
#             submit_btn.click(
#                 fn=submit_text, 
#                 inputs=[input_text, input_creator], 
#                 outputs=[output_label, active_content_id, trigger_appeal_btn]
#             )
            
#             trigger_appeal_btn.click(
#                 fn=lambda: gr.update(visible=True),
#                 inputs=None,
#                 outputs=[appeal_box]
#             )
            
#             appeal_btn.click(
#                 fn=file_appeal,
#                 inputs=[active_content_id, appeal_reason],
#                 outputs=[appeal_status]
#             ).then(
#                 fn=lambda: gr.update(value=""),
#                 inputs=None,
#                 outputs=[appeal_reason]
#             )

#         # TAB 2: USER AUDIT LOG HISTORY
#         with gr.TabItem("My Submission History"):
#             gr.Markdown("### Personal Evaluation Audit Trail")
#             gr.Markdown("Look up your previous submissions associated with your user handle below.")
            
#             with gr.Row():
#                 search_creator_id = gr.Textbox(
#                     label="Enter Your Creator Handle ", 
#                     placeholder="e.g., author-44",
#                     value="creator-44"
#                 )
#                 search_btn = gr.Button("Show Log", variant="secondary")
            
#             history_display = gr.Markdown("Enter your handle above and hit search to pull database records.")
            
#             # Event Wiring (Tab 2)
#             search_btn.click(
#                 fn=fetch_user_history, 
#                 inputs=[search_creator_id], 
#                 outputs=[history_display]
#             )


# if __name__ == "__main__":
#     demo.launch(
#         server_name="0.0.0.0", 
#         server_port=7860,
#         theme=gr.themes.Soft()
#     )

import gradio as gr
import requests

FLASK_URL = "http://localhost:8080"

# =====================================================================
# API CALL HELPERS
# =====================================================================
def submit_text(text, creator_id):
    if not text.strip() or not creator_id.strip():
        return "⚠️ Error: Text and Creator ID cannot be blank.", None, gr.update(visible=False)
    
    try:
        response = requests.post(f"{FLASK_URL}/submit", json={"text": text, "creator_id": creator_id})
        if response.status_code == 200:
            data = response.json()
            
            # Fetch additional system log records to pull the individual underlying signal dimensions
            log_response = requests.get(f"{FLASK_URL}/log")
            s1_score, s2_score = 0.0, 0.0
            if log_response.status_code == 200:
                entries = log_response.json().get("entries", [])
                # Match the current active record by UUID context
                current_record = next((e for e in entries if e.get("content_id") == data["content_id"]), None)
                if current_record:
                    s1_score = current_record.get("llm_score", 0.0)
                    s2_score = current_record.get("stylometric_score", 0.0)

            # Extract clean human-readable header blocks from transparency label
            raw_label = data['label']
            if " > " in raw_label:
                header, description = raw_label.split(" > ", 1)
            else:
                header, description = "Classification Determined", raw_label

            # Calculate an explicit confidence percentage from the combined score context
            raw_confidence = data['confidence']
            if data['attribution'] == "likely_human":
                display_pct = round((1.0 - raw_confidence) * 100)
            elif data['attribution'] == "likely_ai":
                display_pct = round(raw_confidence * 100)
            else:
                display_pct = round((1.0 - abs(0.5 - raw_confidence)) * 100)

            # Structural Layout Template Formatting
            ui_markdown_output = f"## **{header}**\n\n"
            ui_markdown_output += f"{description}\n\n"
            ui_markdown_output += f"--- \n"
            ui_markdown_output += f"**Score Analysis:**\n"
            ui_markdown_output += f"* **Confidence Score:** `{display_pct}%`\n"
            ui_markdown_output += f"* **Combined Core Score:** `{raw_confidence}`\n"
            ui_markdown_output += f"* **Signal 1 (Semantic Probabilities):** `{s1_score}`\n"
            ui_markdown_output += f"* **Signal 2 (Stylometric Heuristics):** `{s2_score}`\n\n"
            ui_markdown_output += f"**Submission ID:** `{data['content_id']}`"

            return (
                ui_markdown_output,
                data['content_id'],
                gr.update(visible=True)  # Reveal the "Dispute This Result" button next to the labels
            )
        elif response.status_code == 429:
            return "🛑 Rate Limit Exceeded: Please wait a minute before trying again.", None, gr.update(visible=False)
        else:
            return f"❌ Error: {response.json().get('error', 'Unknown issue')}", None, gr.update(visible=False)
    except Exception as e:
        return f"💥 Connection Error: Is your Flask app running? ({str(e)})", None, gr.update(visible=False)


def file_appeal(content_id, reasoning):
    if not content_id.strip():
        return "⚠️ Error: Submission ID cannot be blank."
    if len(reasoning) < 10 or len(reasoning) > 500:
        return "⚠️ Validation Error: Appeal reasoning must be between 10 and 500 characters."
        
    try:
        response = requests.post(f"{FLASK_URL}/appeal", json={"content_id": content_id.strip(), "creator_reasoning": reasoning})
        if response.status_code == 200:
            return " Appeal submitted successfully! The submission state has transitioned to 'under_review'."
        else:
            return f"❌ Error: {response.json().get('error', 'Processing failure')}"
    except Exception as e:
        return f"💥 Connection Error: {str(e)}"


def fetch_user_history(creator_id):
    if not creator_id.strip():
        return "⚠️ Error: Please enter a valid Creator Handle to look up history."
        
    try:
        response = requests.get(f"{FLASK_URL}/log")
        if response.status_code == 200:
            entries = response.json().get("entries", [])
            
            # Filter logs down to matches for this exact creator handle
            user_entries = [e for e in entries if str(e.get("creator_id")).strip() == creator_id.strip()]
            
            if not user_entries:
                return f"No submission records found for handle: `{creator_id}`"
                
            # Render out the historical log items as scannable markdown blocks
            formatted_output = f"## Audit Log for `{creator_id}` ({len(user_entries)} entries found)\n\n"
            total_entries = len(user_entries)
            # Newest-first from the DB (ORDER BY timestamp DESC); count numbering down so the latest entry shows the highest number
            for offset, case in enumerate(user_entries):
                idx = total_entries - offset
                status_emoji = "⏳" if case.get("status") == "under_review" else "✅"
                
                formatted_output += f"### {status_emoji} Entry #{idx}: `{case['content_id']}`\n"
                formatted_output += f"**Timestamp:** `{case['timestamp']}` | **Status:** `{case['status'].upper()}`\n\n"
                formatted_output += f"> **Text Fragment:**\n> \"{case['text_content'][:200]}...\"\n\n" # Truncated for readability
                formatted_output += f" **Metrics History:**\n"
                formatted_output += f"* Combined Score: `{case['confidence']}` | LLM Signal: `{case['llm_score']}` | Stylometric Signal: `{case['stylometric_score']}`\n"
                
                if case.get("appeal_reasoning"):
                    formatted_output += f"🛡️ **Filed Appeal Reason:** *\"{case['appeal_reasoning']}\"*\n"
                formatted_output += "---\n\n"
                
            return formatted_output
        return "❌ Failed to fetch structural system logs."
    except Exception as e:
        return f" Connection Error: {str(e)}"


# =====================================================================
# GRADIO INTERFACE LAYOUT
# =====================================================================
with gr.Blocks(title="Provenance Guard Dashboard") as demo:
    gr.Markdown("# Provenance Guard")
    gr.Markdown("We analyze text structure and style to verify original human writing, provide clear breakdowns of our reasoning, and offer an instant human review process if you ever want to dispute a result.")
    
    with gr.Tabs() as tabs:
        # TAB 1: CREATOR WORKSPACE
        with gr.TabItem("Work Evaluation", id="evaluation_tab"):
            gr.Markdown("### Submit Text for Evaluation")
            
            with gr.Row():
                # Left Side: Submissions
                with gr.Column(scale=2):
                    input_creator = gr.Textbox(label="Creator Handle (case-sensitive)", placeholder="e.g., author-44", value="creator-44")
                    input_text = gr.Textbox(label="Raw Writing Content", placeholder="Paste your text block here...", lines=8)
                    submit_btn = gr.Button("Submit Entry", variant="primary")
                
                # Right Side: Targeted Label Results
                with gr.Column(scale=1):
                    gr.Markdown("### Evaluation Results")
                    output_label = gr.Markdown("*Awaiting submission text analysis...*")
                    trigger_appeal_btn = gr.Button("Dispute This Result", variant="secondary", visible=False)
            
            active_content_id = gr.State()

            # Event Wiring (Tab 1)
            submit_btn.click(
                fn=submit_text, 
                inputs=[input_text, input_creator], 
                outputs=[output_label, active_content_id, trigger_appeal_btn]
            )
            
            # Clicking dispute navigates to the appeal tab and updates the target ID input
            trigger_appeal_btn.click(
                fn=lambda content_id: (gr.update(selected="appeal_tab"), content_id),
                inputs=[active_content_id],
                outputs=[tabs, gr.Textbox(visible=True)]
            )

        # TAB 2: USER AUDIT LOG HISTORY
        with gr.TabItem("My Submission History", id="history_tab"):
            gr.Markdown("### Personal Evaluation Audit Trail")
            gr.Markdown("Look up your previous submissions associated with your user handle below.")
            
            with gr.Row():
                search_creator_id = gr.Textbox(
                    label="Enter Your Creator Handle ", 
                    placeholder="e.g., author-44",
                    value="creator-44"
                )
                search_btn = gr.Button("Show Log", variant="secondary")
            
            history_display = gr.Markdown("Enter your handle above and hit search to pull database records.")
            
            # Event Wiring (Tab 2)
            search_btn.click(
                fn=fetch_user_history, 
                inputs=[search_creator_id], 
                outputs=[history_display]
            )

        # TAB 3: DEDICATED APPEALS MANAGEMENT
        with gr.TabItem("File an Appeal", id="appeal_tab"):
            gr.Markdown("### File a Formal System Appeal")
            gr.Markdown("Provide context about your writing background or language patterns to route this record to human verification.")
            
            with gr.Group():
                appeal_id = gr.Textbox(label="Submission ID (content_id UUID)", placeholder="Paste the content_id here...")
                appeal_reason = gr.Textbox(label="Your Explanation Statement (10-500 characters)", placeholder="Why is this evaluation inaccurate?...", lines=4)
                appeal_btn = gr.Button("Submit Official Appeal", variant="stop")
                appeal_status = gr.Markdown()
            
            # Event Wiring (Tab 3)
            appeal_btn.click(
                fn=file_appeal,
                inputs=[appeal_id, appeal_reason],
                outputs=[appeal_status]
            ).then(
                fn=lambda: (gr.update(value=""), gr.update(value="")),
                inputs=None,
                outputs=[appeal_id, appeal_reason]
            )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860,
        theme=gr.themes.Soft()
    )