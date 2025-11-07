package com.example.pcproject.controller;

import com.example.pcproject.service.AiService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;

import java.util.Map;
import java.util.HashMap;
import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/ai")
public class AiController {

    private final AiService aiService;

    @PostMapping("/chat")
    public ResponseEntity<?> chat(@RequestBody Map<String, Object> chatRequest) {
        try {
            // ✅ messages 필드만 추출
            @SuppressWarnings("unchecked")
            List<Map<String, String>> messages = (List<Map<String, String>>) chatRequest.get("messages");

            // ✅ [2주차 세션 기능 추가 대비]
            // 지금은 없어도 되고, 나중에 프론트에서 session_id 같이 보내면 바로 활성화 가능
            /*
            String sessionId = (String) chatRequest.get("session_id");
            Map<String, Object> result = aiService.chat(messages, sessionId);
            */

            // ✅ 현재 버전: 세션 없이 단순 messages만 전달
            Map<String, Object> result = aiService.chat(messages);

            return ResponseEntity.ok(result);

        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of(
                    "success", false,
                    "message", "AI 처리 중 오류가 발생했습니다.",
                    "detail", e.getMessage()
            ));
        }
    }
}
