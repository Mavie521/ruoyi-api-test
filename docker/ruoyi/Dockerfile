# =============================================
# 构建 RuoYi 后端 Docker 镜像
# 多阶段构建：编译 → 运行，你不需要装 Java
# =============================================

# ---- 阶段一：编译 ----
FROM maven:3.9-eclipse-temurin-17 AS builder

ARG RUOYI_VERSION=v3.9.2
WORKDIR /build

# 克隆若依后端源码（已确认 v3.9.2 tag 存在）
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/* && \
    git clone --depth 1 --branch ${RUOYI_VERSION} \
        https://github.com/yangzongzhuan/RuoYi-Vue.git .

# Maven 编译，跳过测试
RUN mvn clean package -DskipTests -q

# ---- 阶段二：运行 ----
FROM eclipse-temurin:17-jre

WORKDIR /app

# 从编译阶段复制 JAR
COPY --from=builder /build/ruoyi-admin/target/ruoyi-admin.jar app.jar

# 安装 curl（用于健康检查）+ 中文时区
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

ENV TZ=Asia/Shanghai
EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
