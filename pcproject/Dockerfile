<<<<<<< HEAD
FROM gradle:8.7-jdk17 AS builder
WORKDIR /app
COPY . .
RUN ./gradlew clean build -x test

FROM openjdk:17-jdk-slim
WORKDIR /app
COPY --from=builder /app/build/libs/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
=======
# 1. Java 21 실행 환경(JRE)을 가져옵니다.
FROM eclipse-temurin:21-jre-jammy

# 2. 빌드된 JAR 파일이 복사될 위치를 지정합니다.
ARG JAR_FILE=build/libs/*.jar

# 3. JAR 파일을 컨테이너 안으로 복사하고 이름을 app.jar로 변경합니다.
COPY ${JAR_FILE} app.jar

# 4. Spring Boot 앱이 사용하는 8080 포트를 엽니다.
EXPOSE 8080

# 5. 컨테이너가 시작될 때 이 명령어를 실행하여 Java 앱을 켭니다.
ENTRYPOINT ["java", "-jar", "/app.jar"]
>>>>>>> 0d8dc81 (back)
