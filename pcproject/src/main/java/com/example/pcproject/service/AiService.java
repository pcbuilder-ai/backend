package com.example.pcproject.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@Slf4j
@RequiredArgsConstructor
public class AiService {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${openai.api.key:}")
    private String openAiApiKey;

    @Value("${openai.api.base:https://api.openai.com}")
    private String openAiBaseUrl;

    @Value("${openai.api.model:gpt-4o-mini}")
    private String defaultModel;

    @Value("${openai.org:}")
    private String openAiOrg;

    @Value("${openai.project:}")
    private String openAiProject;

    public Map<String, Object> chat(List<Map<String, String>> messages, String model, Integer maxTokens, Double temperature) {
        if (openAiApiKey == null || openAiApiKey.isBlank()) {
            return error("OPENAI_API_KEY is not configured.");
        }

        try {
            String url = openAiBaseUrl + "/v1/chat/completions";

            Map<String, Object> payload = new HashMap<>();
            payload.put("model", (model == null || model.isBlank()) ? defaultModel : model);
            payload.put("messages", messages);
            if (maxTokens != null) payload.put("max_tokens", maxTokens);
            if (temperature != null) payload.put("temperature", temperature);

            String json = objectMapper.writeValueAsString(payload);

            HttpRequest.Builder builder = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .timeout(Duration.ofSeconds(60))
                    .header("Authorization", "Bearer " + openAiApiKey)
                    .header("Content-Type", "application/json; charset=UTF-8");

            if (openAiOrg != null && !openAiOrg.isBlank()) {
                builder.header("OpenAI-Organization", openAiOrg);
            }
            if (openAiProject != null && !openAiProject.isBlank()) {
                builder.header("OpenAI-Project", openAiProject);
            }

            HttpRequest request = builder
                    .POST(HttpRequest.BodyPublishers.ofString(json, StandardCharsets.UTF_8))
                    .build();

            HttpClient client = HttpClient.newHttpClient();
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));

            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                return objectMapper.readValue(response.body(), new TypeReference<Map<String, Object>>() {});
            }

            log.warn("OpenAI API error: status={}, body={}", response.statusCode(), response.body());
            Map<String, Object> error = new HashMap<>();
            error.put("success", false);
            error.put("status", response.statusCode());
            error.put("message", "OpenAI API request failed");
            error.put("body", safeBody(response.body()));
            return error;
        } catch (Exception e) {
            log.error("OpenAI API call failed", e);
            return error(e.getMessage());
        }
    }

    private Map<String, Object> error(String message) {
        Map<String, Object> map = new HashMap<>();
        map.put("success", false);
        map.put("message", message);
        return map;
    }

    private Object safeBody(String body) {
        try {
            return objectMapper.readValue(body, new TypeReference<Map<String, Object>>() {});
        } catch (Exception ignore) {
            return body;
        }
    }
}



