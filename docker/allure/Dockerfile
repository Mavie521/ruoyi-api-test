# =============================================
# Allure 报告生成器镜像
# 从 Maven Central 下载 Allure CLI（国内友好）
# =============================================
FROM eclipse-temurin:17-jre

# JVM 默认编码设为 UTF-8（修复 Allure 环境块中文乱码）
ENV LANG=C.UTF-8
ENV JAVA_TOOL_OPTIONS="-Dfile.encoding=UTF-8"

WORKDIR /app

# 从 Maven 中央仓库下载 Allure（不走 GitHub，国内可访问）
RUN apt-get update && apt-get install -y --no-install-recommends wget unzip && \
    rm -rf /var/lib/apt/lists/* && \
    wget -q -O allure.zip \
        "https://repo1.maven.org/maven2/io/qameta/allure/allure-commandline/2.32.0/allure-commandline-2.32.0.zip" && \
    unzip allure.zip && \
    ln -s /app/allure-2.32.0/bin/allure /usr/local/bin/allure && \
    rm allure.zip

ENTRYPOINT ["allure"]
CMD ["--help"]
