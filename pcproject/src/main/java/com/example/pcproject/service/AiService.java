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

    @Value("${fastapi.url:http://back_py:8000/ai/query}")
    private String fastApiUrl;

    public Map<String, Object> chat(List<Map<String, String>> messages, String model, Integer maxTokens, Double temperature) {
        try {
            // messages만 전달 (불필요한 파라미터 제거)
            Map<String, Object> payload = new HashMap<>();
            payload.put("messages", messages);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(payload, headers);

            ResponseEntity<String> response = restTemplate.exchange(
                    fastApiUrl,
                    HttpMethod.POST,
                    requestEntity,
                    String.class
            );

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
