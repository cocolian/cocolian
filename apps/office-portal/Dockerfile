FROM docker.io/library/python@sha256:2b4f19dae3a777dfc3b76730bda1e82e1f66ab2a2686fa93ca78edbfb4f04ffe
WORKDIR /app
COPY ai-editor.js ai-panel.js ai-panel.css ai-session.css ai_proxy.py ai_review.py server.py render_profile.py editor.json file_open.py file-open.js file-open.css file-open.svg project-homepage.html project-homepage.css community-qrcode.jpg /app/
USER 1000:1000
EXPOSE 8000
CMD ["python", "/app/server.py"]
