import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from app.parser import parse_resume, parse_job_description
from app.llm import optimize_resume
from app.pdf import generate_pdf

# ── Session state init ────────────────────────────────────────────────────────
for key in ("resume_data", "jd_data", "optimization_result", "optimization_error", "pdf_error"):
    if key not in st.session_state:
        st.session_state[key] = None

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Resume Optimizer")
st.markdown("Upload your resume and paste a job description to get an AI-tailored rewrite.")

# ── Step 1: Inputs ────────────────────────────────────────────────────────────
st.subheader("Step 1 — Upload & Parse")

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])

with col2:
    job_description_text = st.text_area("Paste Job Description", height=300)

if st.button("Parse Documents", type="primary"):
    if uploaded_file is None:
        st.warning("Please upload a resume file.")
    elif not job_description_text.strip():
        st.warning("Please paste a job description.")
    else:
        file_ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
        try:
            with st.spinner("Parsing..."):
                st.session_state["resume_data"] = parse_resume(
                    uploaded_file.read(), file_ext
                )
                st.session_state["jd_data"] = parse_job_description(
                    job_description_text
                )
            # Reset any previous optimization when new docs are parsed
            st.session_state["optimization_result"] = None
            st.session_state["optimization_error"] = None
            st.success("Parsing complete.")
        except ValueError as e:
            st.error(f"Parsing failed: {e}")

if st.session_state["resume_data"]:
    with st.expander("Extracted Resume Text"):
        st.text(st.session_state["resume_data"]["raw_text"])
    with st.expander("Detected Resume Sections"):
        st.json(st.session_state["resume_data"]["sections"])

if st.session_state["jd_data"]:
    with st.expander("Job Description"):
        st.text(st.session_state["jd_data"]["raw_text"])

# ── Step 2: Optimize ──────────────────────────────────────────────────────────
st.divider()
st.subheader("Step 2 — Optimize with AI")

both_parsed = (
    st.session_state["resume_data"] is not None
    and st.session_state["jd_data"] is not None
)

if st.button("Optimize Resume", type="primary", disabled=not both_parsed):
    st.session_state["optimization_result"] = None
    st.session_state["optimization_error"] = None

    with st.spinner("Optimizing resume with GPT-4o-mini..."):
        result = optimize_resume(
            st.session_state["resume_data"],
            st.session_state["jd_data"],
        )

    if "error" in result:
        st.session_state["optimization_error"] = result["error"]
    else:
        st.session_state["optimization_result"] = result

if st.session_state["optimization_error"]:
    st.error(st.session_state["optimization_error"])

if st.session_state["optimization_result"]:
    result = st.session_state["optimization_result"]

    st.success("Resume optimized successfully.")

    # ── Contact + Keywords summary row ────────────────────────
    contact = result.get("contact") or {}
    contact_parts = [v for v in [
        contact.get("phone", ""),
        contact.get("email", ""),
        contact.get("location", ""),
        contact.get("linkedin", ""),
        contact.get("github", ""),
    ] if v.strip()]
    if contact_parts:
        st.markdown(f"**Contact detected:** {' &nbsp;|&nbsp; '.join(contact_parts)}")

    keywords = result.get("keywords_added", [])
    if keywords:
        st.info(f"**Keywords incorporated:** {', '.join(keywords)}")

    with st.expander("Full Optimized Resume", expanded=True):
        st.text(result.get("optimized_text", ""))

    with st.expander("Summary"):
        st.write(result.get("summary", ""))

    with st.expander("Experience"):
        st.write(result.get("experience", ""))

    with st.expander("Education"):
        st.write(result.get("education", ""))

    if result.get("projects"):
        with st.expander("Projects"):
            st.write(result.get("projects", ""))

    with st.expander("Skills"):
        st.write(result.get("skills", ""))

# ── Step 3: Download PDF ───────────────────────────────────────────────────────
st.divider()
st.subheader("Step 3 — Download as PDF")

if st.session_state["optimization_result"]:
    if st.button("Generate PDF", type="primary"):
        st.session_state["pdf_error"] = None
        with st.spinner("Generating PDF..."):
            try:
                pdf_bytes = generate_pdf(st.session_state["optimization_result"])
                st.download_button(
                    label="Download Resume PDF",
                    data=pdf_bytes,
                    file_name="optimized_resume.pdf",
                    mime="application/pdf",
                )
            except RuntimeError as e:
                st.session_state["pdf_error"] = str(e)

    if st.session_state["pdf_error"]:
        st.error(st.session_state["pdf_error"])
else:
    st.info("Complete Step 2 to enable PDF download.")
