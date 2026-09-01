FROM node:20-alpine AS builder

WORKDIR /app

COPY apps/frontend/package.json ./apps/frontend/package.json
RUN cd apps/frontend && npm install

COPY apps/frontend ./apps/frontend

WORKDIR /app/apps/frontend
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

COPY --from=builder /app/apps/frontend/.next/standalone ./
COPY --from=builder /app/apps/frontend/.next/static ./.next/static
COPY --from=builder /app/apps/frontend/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
