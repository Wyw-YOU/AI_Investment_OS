/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    // 代理 /api/* 请求到后端 FastAPI 服务
    // 本地开发: backend 跑在 8000 端口
    // Docker: backend 容器名为 backend，端口 8000
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
