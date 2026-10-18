FROM docker.io/library/python@sha256:2b4f19dae3a777dfc3b76730bda1e82e1f66ab2a2686fa93ca78edbfb4f04ffe
WORKDIR /app
COPY server.py editor.json file_open.py file-open.js file-open.css file-open.svg /app/
USER 1000:1000
EXPOSE 8000
CMD ["python", "/app/server.py"]
