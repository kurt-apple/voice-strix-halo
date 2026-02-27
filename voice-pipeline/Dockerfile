FROM oven/bun:1

WORKDIR /app

COPY package.json .
RUN bun install

COPY src/ ./src/
COPY tsconfig.json .

EXPOSE 10501

CMD ["bun", "run", "src/index.ts"]
