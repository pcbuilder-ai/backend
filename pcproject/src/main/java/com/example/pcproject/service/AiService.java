package com.example.pcproject.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@Slf4j
public class AiService {

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final RestTemplate restTemplate = new RestTemplate();

    // FastAPI 서버 주소 (도커 컨테이너명 back_py 기준)
    @Value("${fastapi.url:http://back_py:8000/ai/query}")
    private String fastApiUrl;

    /**
     * FastAPI에 messages (추후 session_id 포함) 전달하여 AI 응답을 받아옴
     */
    public Map<String, Object> chat(List<Map<String, String>> messages /*, String sessionId */) {
        try {
            // ✅ FastAPI로 전달할 payload 구성
            Map<String, Object> payload = new HashMap<>();
            payload.put("messages", messages);

            /*
            ✅ [2주차 세션 기능 추가 시 여기에 한 줄만 추가]
            if (sessionId != null) {
                payload.put("session_id", sessionId);
            }
            */

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(payload, headers);

            // ✅ FastAPI 호출
            ResponseEntity<String> response = restTemplate.exchange(
                    fastApiUrl,
                    HttpMethod.POST,
                    requestEntity,
                    String.class
            );

            // ✅ 정상 응답 처리
            if (response.getStatusCode().is2xxSuccessful()) {
                return objectMapper.readValue(response.getBody(), new TypeReference<Map<String, Object>>() {});
            } else {
                log.error("FastAPI error: {} - {}", response.getStatusCode(), response.getBody());
                return Map.of(
                        "success", false,
                        "message", "FastAPI 응답 실패",
                        "status", response.getStatusCodeValue(),
                        "body", response.getBody()
                );
            }

        } catch (Exception e) {
            log.error("FastAPI 호출 실패", e);
            return Map.of(
                    "success", false,
                    "message", "FastAPI 호출 중 오류 발생",
                    "detail", e.getMessage()
            );
        }
    }
}
