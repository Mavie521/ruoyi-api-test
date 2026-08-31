# =============================================
# RuoYi 后端 v3.9.2 — 使用本地编译好的 JAR
# 从 Windows 编译后 SCP 到 Rocky，最可靠
# =============================================

FROM eclipse-temurin:17-jre
WORKDIR /app

# 从构建上下文复制本地 JAR（不走网络下载）
COPY jar/ruoyi-admin.jar app.jar

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV TZ=Asia/Shanghai
EXPOSE 8080

# 启动参数直接覆盖所有配置（优先级最高）
ENTRYPOINT ["java", "-jar", "app.jar"]
