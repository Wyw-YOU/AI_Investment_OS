FROM mirror.ccs.tencentyun.com/library/node:20-alpine AS deps
WORKDIR /app
# 腾讯云 npm 镜像
RUN npm config set registry https://mirrors.tencent.com/npm/
COPY package.json package-lock.json* ./
RUN npm ci || npm install

FROM mirror.ccs.tencentyun.com/library/node:20-alpine AS builder
WORKDIR /app
ENV BACKEND_URL=http://backend:8000
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM mirror.ccs.tencentyun.com/library/node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
