import os
import gradio as gr
from analyzer import analyze_feedback, analyze_batch

def format_single_result(result: dict) -> str:
    if not result["success"]:
        return f"**Error:** {result['error']}"

    d         = result["data"]
    sentiment = d.get("sentiment", "N/A")
    emotion   = d.get("emotion", "N/A")
    score     = d.get("sentiment_score", 0)
    conf      = d.get("confidence", "N/A")
    priority  = d.get("priority", "N/A")
    summary   = d.get("summary", "")
    topics    = d.get("key_topics", [])
    positives = d.get("positive_aspects", [])
    negatives = d.get("negative_aspects", [])
    rec       = d.get("actionable_recommendation", "")

    sentiment_map = {
        "Positive": "🟢 Positive",
        "Negative": "🔴 Negative",
        "Neutral":  "⚪ Neutral",
        "Mixed":    "🟡 Mixed",
    }
    priority_map = {
        "High":   "🔴 High — Immediate action needed",
        "Medium": "🟡 Medium — Address this week",
        "Low":    "🟢 Low — Monitor for trends",
    }

    score_pct = int((score + 1) / 2 * 100)
    filled    = int(score_pct / 5)
    bar       = "▓" * filled + "░" * (20 - filled)
    pos_lines = "\n".join(f"- {p}" for p in positives) if positives else "- None identified"
    neg_lines = "\n".join(f"- {n}" for n in negatives) if negatives else "- None identified"
    topic_str = "  ·  ".join(topics) if topics else "None identified"

    return f"""
**SUMMARY**
{summary}

---

| Field | Value |
|:--|:--|
| Sentiment | {sentiment_map.get(sentiment, sentiment)} |
| Emotion | {emotion} |
| Score | {score:+.2f} out of 1.0 ({score_pct}%) |
| Confidence | {conf} |
| Priority | {priority_map.get(priority, priority)} |

**SENTIMENT SCORE**
`{bar}` {score_pct}%

---

**KEY TOPICS**
{topic_str}

**POSITIVE ASPECTS**
{pos_lines}

**ISSUES IDENTIFIED**
{neg_lines}

---

**RECOMMENDATION**
{rec}
"""


def run_single(text: str) -> str:
    if not text or len(text.strip()) < 10:
        return "Please enter at least 10 characters of feedback."
    return format_single_result(analyze_feedback(text))


def run_batch(text: str) -> str:
    if not text or len(text.strip()) < 5:
        return "Please enter at least one feedback."
    results = analyze_batch(text)
    if not results:
        return "No valid feedbacks found. Each feedback should be on a new line."

    sentiments = [r["data"]["sentiment"] for r in results if r["success"]]
    total = len(results)
    pos = sentiments.count("Positive")
    neg = sentiments.count("Negative")
    neu = sentiments.count("Neutral")
    mix = sentiments.count("Mixed")

    out = f"""
**BATCH SUMMARY — {total} Reviews Analyzed**

| 🟢 Positive | 🔴 Negative | ⚪ Neutral | 🟡 Mixed |
|:---:|:---:|:---:|:---:|
| {pos} | {neg} | {neu} | {mix} |

---
"""
    for r in results:
        preview = r["original_text"][:90] + ("..." if len(r["original_text"]) > 90 else "")
        out += f"\n**Review #{r['index']}** — {preview}\n"
        out += format_single_result(r)
        out += "\n---\n"
    return out


S_POS   = "The customer support team was incredibly helpful and resolved my issue within 10 minutes. The product itself exceeded my expectations. Will definitely recommend to friends!"
S_NEG   = "I've been waiting 3 weeks for my order and still no update. Customer service is unreachable and when I finally got through, they couldn't tell me anything useful. Very disappointed."
S_MIX   = "The product quality is excellent and works exactly as described. However, the delivery took much longer than expected and the packaging was damaged. Mixed feelings overall."
S_BATCH = """Great product, fast shipping, very satisfied with the purchase!
Terrible experience. The app keeps crashing and support never responds.
Average service, nothing special but gets the job done.
I love the new features but the price increase is too much.
Delivery was late but the product quality made up for it."""

# ── CSS Variables Fix ──
# Ab yeh Gradio ke native dark mode toggle ke sath sync karega
CSS = """
:root {
    --c-bg-input: rgba(0,0,0,0.05);
    --c-border: rgba(0,0,0,0.1);
    --c-text-main: #1e293b;
    --c-text-muted: #64748b;
    --c-accent: #6366f1;
    --c-table-head: #f1f5f9;
}

/* Gradio's Dark Mode Class */
.dark {
    --c-bg-input: rgba(255,255,255,0.06);
    --c-border: rgba(255,255,255,0.12);
    --c-text-main: rgba(255,255,255,0.9);
    --c-text-muted: rgba(255,255,255,0.5);
    --c-accent: #818cf8;
    --c-table-head: rgba(129,140,248,0.15);
}

* { font-family: 'Inter', sans-serif !important; }

.gradio-container { max-width: 850px !important; margin: 0 auto !important; }

/* Custom Markdown Styling */
.md-out table { 
    width: 100% !important; 
    border-collapse: collapse !important; 
    margin: 15px 0 !important; 
    border: 1px solid var(--c-border) !important;
}
.md-out th { 
    background: var(--c-table-head) !important; 
    padding: 12px !important; 
    text-align: left !important; 
    color: var(--c-accent) !important;
}
.md-out td { 
    padding: 12px !important; 
    border-bottom: 1px solid var(--c-border) !important;
    color: var(--c-text-main) !important;
}
footer { display: none !important; }
"""

def format_single_result(result: dict) -> str:
    if not result["success"]:
        return f"### ⚠️ Error\n{result['error']}"

    d = result["data"]
    sentiment_map = {"Positive": "🟢 Positive", "Negative": "🔴 Negative", "Neutral": "⚪ Neutral", "Mixed": "🟡 Mixed"}
    priority_map = {"High": "🔴 High", "Medium": "🟡 Medium", "Low": "🟢 Low"}

    score = d.get("sentiment_score", 0)
    score_pct = int((score + 1) / 2 * 100)
    bar = "▓" * int(score_pct / 5) + "░" * (20 - int(score_pct / 5))

    return f"""
### SUMMARY
{d.get('summary', '')}

| Field | Value |
|:---|:---|
| **Sentiment** | {sentiment_map.get(d.get('sentiment'), d.get('sentiment'))} |
| **Emotion** | {d.get('emotion', 'N/A')} |
| **Score** | {score:+.2f} ({score_pct}%) |
| **Priority** | {priority_map.get(d.get('priority'), d.get('priority'))} |

**Score Meter:** `{bar}` {score_pct}%

**Key Topics:** {", ".join(d.get('key_topics', []))}

**✅ Positive:** {", ".join(d.get('positive_aspects', [])) if d.get('positive_aspects') else "None"}
**❌ Issues:** {", ".join(d.get('negative_aspects', [])) if d.get('negative_aspects') else "None"}

---
**💡 Recommendation:** {d.get('actionable_recommendation', 'N/A')}
"""


# UI Components
with gr.Blocks(theme=gr.themes.Soft(primary_hue="indigo"), css=CSS, title="AI Feedback Analyzer") as demo:
    gr.Markdown("# 🔍 Customer Feedback Analyzer")
    gr.Markdown("AI-powered sentiment analysis and actionable business insights &nbsp;·&nbsp; Built by [**Muhammad Zeeshan**](https://zeeshan-portfolio-amber.vercel.app) &nbsp;·&nbsp; [LinkedIn](https://linkedin.com/in/zeeshanofficial) &nbsp;·&nbsp; [GitHub](https://github.com/dev-mzeeshan)")

    with gr.Tabs():
        # with gr.TabItem("Single Review"):
        #     single_input = gr.Textbox(label="Enter Feedback", placeholder="Type or paste here...", lines=4)
        #     with gr.Row():
        #         btn = gr.Button("Analyze", variant="primary")
        #         clear = gr.Button("Clear")
        #     output = gr.Markdown(elem_classes=["md-out"])
            
        #     btn.click(run_single, inputs=single_input, outputs=output)
        #     clear.click(lambda: ("", ""), outputs=[single_input, output])

        # with gr.TabItem("Batch Analysis"):
        #     batch_input = gr.Textbox(label="Bulk Reviews (one per line)", lines=8)
        #     batch_btn = gr.Button("Analyze All", variant="primary")
        #     batch_output = gr.Markdown(elem_classes=["md-out"])
            
        #     batch_btn.click(run_batch, inputs=batch_input, outputs=batch_output)
        with gr.TabItem("Single Review"):
            gr.Markdown(
                "<p style='font-size:13px;color:var(--c-text-muted);margin:0 0 16px'>Paste one customer review to get sentiment, emotion, key topics, and an actionable recommendation.</p>"
            )
            single_input = gr.Textbox(
                label="Customer Feedback",
                placeholder="Paste customer feedback here...",
                lines=5,
                max_lines=14,
            )
            with gr.Row():
                analyze_btn = gr.Button("Analyze", variant="primary", scale=3)
                clear_btn   = gr.Button("Clear",   variant="secondary", scale=1)

            gr.Markdown(
                "<p style='font-size:12px;color:var(--c-text-faint);margin:12px 0 8px'>Try a sample:</p>"
            )
            with gr.Row():
                s_pos = gr.Button("Positive review", size="sm")
                s_neg = gr.Button("Negative review", size="sm")
                s_mix = gr.Button("Mixed review",    size="sm")

            single_out = gr.Markdown(
                value="*Analysis will appear here after you click Analyze.*",
                elem_classes=["md-out"],
            )

            analyze_btn.click(run_single, inputs=single_input, outputs=single_out)
            clear_btn.click(
                lambda: ("", "*Analysis will appear here after you click Analyze.*"),
                outputs=[single_input, single_out],
            )
            s_pos.click(lambda: S_POS, outputs=single_input)
            s_neg.click(lambda: S_NEG, outputs=single_input)
            s_mix.click(lambda: S_MIX, outputs=single_input)

        with gr.TabItem("Batch Analysis"):
            gr.Markdown(
                "<p style='font-size:13px;color:var(--c-text-muted);margin:0 0 16px'>Paste multiple reviews — one per line. Get per-review breakdowns plus an overall summary table.</p>"
            )
            batch_input = gr.Textbox(
                label="Multiple Reviews (one per line)",
                placeholder="Review 1...\nReview 2...\nReview 3...",
                lines=7,
                max_lines=24,
            )
            with gr.Row():
                batch_btn       = gr.Button("Analyze All", variant="primary", scale=3)
                load_sample_btn = gr.Button("Load Sample", variant="secondary", scale=1)

            batch_out = gr.Markdown(
                value="*Results will appear here after you click Analyze All.*",
                elem_classes=["md-out"],
            )

            batch_btn.click(run_batch, inputs=batch_input, outputs=batch_out)
            load_sample_btn.click(lambda: S_BATCH, outputs=batch_input)

        gr.Markdown(
        "<p style='font-size:12px;color:var(--c-text-faint);text-align:center;margin-top:24px'>Powered by Groq API &nbsp;·&nbsp; Llama 3.3 70B &nbsp;·&nbsp; Gradio 5 &nbsp;·&nbsp; <a href='https://github.com/dev-mzeeshan/customer-feedback-analyzer' target='_blank'>View on GitHub</a></p>"
    )

if __name__ == "__main__":
    # Render deployment configuration
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port, ssr_mode=False)