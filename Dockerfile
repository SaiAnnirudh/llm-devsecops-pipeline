FROM nginx:alpine
COPY app/ /usr/share/nginx/html/
COPY llm_validation_results.json /usr/share/nginx/html/