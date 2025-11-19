package com.example.pcproject.controller;

import com.example.pcproject.service.AiService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/ai")
public class AiController {

    private final AiService aiService;

    @PostMapping("/chat")
    public ResponseEntity<?> chat(@RequestBody Map<String, Object> chatRequest, HttpServletRequest request) {
        try {
            // ✅ 프론트에서 넘어온 "message" 값만 추출
            String message = (String) chatRequest.get("message");

            if (message == null || message.isBlank()) {
                return ResponseEntity.badRequest().body(Map.of(
                        "success", false,
                        "message", "message 필드가 비어 있습니다."
                ));
            }

            // ✅ Spring 세션 ID 사용 (자동 생성 or 기존 유지)
            String sessionId = request.getSession().getId();

            // ✅ FastAPI로 요청 (message + sessionId 전달)
            Map<String, Object> result = aiService.chat(message, sessionId);

            return ResponseEntity.ok(result);

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(500).body(Map.of(
                    "success", false,
                    "message", "AI 처리 중 오류가 발생했습니다.",
                    "detail", e.getMessage()
            ));
        }
    }
}
