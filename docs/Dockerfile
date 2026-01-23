FROM squidfunk/mkdocs-material:latest

WORKDIR /docs

# Copy documentation files
COPY . /docs/

EXPOSE 8000

CMD ["serve", "--dev-addr=0.0.0.0:8000"]
