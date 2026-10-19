ARG BASE_IMAGE=res.cocolian.cn/cocolian/office-portal@sha256:c4e90a07ac09ae88061a44bda5db4f25348498fdd6678f5fbab903ab0df51792
FROM ${BASE_IMAGE}
COPY server.py render_profile.py /app/
